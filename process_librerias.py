"""
process_librerias.py
Lee todos los CSV en raw_data/, filtra librerías (CIIU 4761) para las provincias
indicadas, georreferencia por parroquia usando el shapefile nxparroquias,
genera CSV limpio en cleaned/ y mapas por provincia + combinado en outputs/.
"""

import os
import glob
import pandas as pd
import geopandas as gpd
import unicodedata
import folium
from folium.plugins import MarkerCluster

# --- Config ---
RAW_DIR = "raw_data"
SHP_PARROQUIAS = "datos_shp/nxparroquias.shp"
CLEAN_DIR = "cleaned"
OUT_DIR = "outputs"

PROVINCIAS = ["MORONA SANTIAGO", "TUNGURAHUA"]   # provincias a considerar (textual)
CIIU_FRAGMENT = "4761"   # criterio para librerías (busca este fragmento en CODIGO_CIIU)

# Salidas
OUT_CSV_ALL = os.path.join(CLEAN_DIR, "librerias_georef_all.csv")

# --- Utilities ---
def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().upper()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return texto

def ensure_dirs():
    for d in (RAW_DIR, CLEAN_DIR, OUT_DIR, os.path.dirname(SHP_PARROQUIAS) or "."):
        if d and not os.path.exists(d):
            os.makedirs(d)

# --- Cargar todos los CSV del raw_data ---
def load_raw_csvs():
    files = glob.glob(os.path.join(RAW_DIR, "*.csv"))
    if not files:
        raise SystemExit("No se encontraron CSV en raw_data/. Pone tus archivos y reintenta.")
    frames = []
    for f in files:
        print("Leyendo:", f)
        df = pd.read_csv(f, sep="|", dtype=str, low_memory=False)
        # Normaliza nombre columna
        df.columns = df.columns.str.strip()
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    print(f"Registros totales cargados: {len(combined)}")
    return combined

# --- Main ---
def main():
    ensure_dirs()

    # 1) leer CSVs y filtrar por provincia y CIIU
    df = load_raw_csvs()
    # Filtrar por las provincias de la lista (comparación robusta)
    df["prov_clean"] = df["DESCRIPCION_PROVINCIA_EST"].apply(lambda x: normalizar(x))
    provincias_norm = [normalizar(p) for p in PROVINCIAS]
    df = df[df["prov_clean"].isin(provincias_norm)].copy()
    print("Registros tras filtrar provincias:", len(df))

    # Filtrar por CIIU (contiene fragmento 4761)
    df = df[df["CODIGO_CIIU"].str.contains(CIIU_FRAGMENT, na=False)].copy()
    print("Registros tras filtrar CIIU librerías:", len(df))

    if df.empty:
        print("No hay registros que cumplan el filtro. Revisar CSV o código CIIU.")
        return

    # Normalizar campos para merge con shapefile
    df["prov_norm"] = df["DESCRIPCION_PROVINCIA_EST"].apply(normalizar)
    df["cant_norm"] = df["DESCRIPCION_CANTON_EST"].apply(normalizar)
    df["parr_norm"] = df["DESCRIPCION_PARROQUIA_EST"].apply(normalizar)

    # 2) leer shapefile de parroquias
    print("Cargando shapefile de parroquias:", SHP_PARROQUIAS)
    par = gpd.read_file(SHP_PARROQUIAS, engine="pyogrio")
    # Si el shapefile no tiene CRS, asumimos UTM (32717) como antes — pero si ya lo tiene, respetamos
    if par.crs is None:
        par.set_crs(epsg=32717, inplace=True)
    # Lo convertimos a 4326 para trabajar en lat/lon
    par = par.to_crs(epsg=4326)
    # Normalizar columnas del shapefile para unir
    par["prov_norm"] = par["DPA_DESPRO"].apply(normalizar)
    par["cant_norm"] = par["DPA_DESCAN"].apply(normalizar)
    par["parr_norm"] = par["DPA_DESPAR"].apply(normalizar)

    # 3) merge por provincia+cantón+parroquia
    merged = df.merge(
        par[["prov_norm","cant_norm","parr_norm","geometry"]],
        on=["prov_norm","cant_norm","parr_norm"],
        how="left",
        validate="m:1"
    )
    gdf = gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")

    # 4) calcular centroides correctamente: proyectar a métrica, calcular, volver a 4326
    try:
        gdf_metric = gdf.to_crs(epsg=32717)
        gdf_metric["centroid"] = gdf_metric.geometry.centroid
        centroids = gdf_metric.set_geometry("centroid").to_crs(epsg=4326)
        gdf["lat"] = centroids.geometry.y
        gdf["lon"] = centroids.geometry.x
    except Exception as e:
        print("Error al proyectar/centroides:", e)
        # fallback: intentar centroid directamente (menos recomendado)
        gdf["centroid"] = gdf.geometry.centroid
        gdf["lat"] = gdf.centroid.y
        gdf["lon"] = gdf.centroid.x

    # 5) Guardar CSV limpio combinado y por provincia
    cols_out = [
        "NUMERO_RUC","RAZON_SOCIAL","CODIGO_CIIU",
        "DESCRIPCION_PROVINCIA_EST","DESCRIPCION_CANTON_EST","DESCRIPCION_PARROQUIA_EST",
        "lat","lon"
    ]
    df_out = gdf[cols_out].copy()
    df_out.to_csv(OUT_CSV_ALL, index=False, encoding="utf-8")
    print("CSV combinado guardado en:", OUT_CSV_ALL)

    # También guardar por provincia archivos separados
    for prov in PROVINCIAS:
        pn = normalizar(prov)
        sub = df_out[df_out["DESCRIPCION_PROVINCIA_EST"].apply(lambda x: normalizar(x)) == pn]
        out_path = os.path.join(CLEAN_DIR, f"librerias_georef_{pn.replace(' ','_')}.csv")
        sub.to_csv(out_path, index=False, encoding="utf-8")
        print(f"Guardado {len(sub)} registros para {prov} en: {out_path}")

    # 6) Crear mapas (por provincia y combinado) con marker cluster
    def crear_mapa(df_map, fname, center=[-2.3, -78.0], zoom=8):
        m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")
        marker_cluster = MarkerCluster().add_to(m)
        for _, r in df_map.dropna(subset=["lat","lon"]).iterrows():
            popup = folium.Popup(
                f"<b>{r['RAZON_SOCIAL']}</b><br>RUC: {r['NUMERO_RUC']}<br>{r['DESCRIPCION_PROVINCIA_EST']} - {r['DESCRIPCION_CANTON_EST']} - {r['DESCRIPCION_PARROQUIA_EST']}",
                max_width=300
            )
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=5,
                color="blue",
                fill=True,
                fill_color="cyan",
                fill_opacity=0.9,
                popup=popup
            ).add_to(marker_cluster)
        out_file = os.path.join(OUT_DIR, fname)
        m.save(out_file)
        print("Mapa guardado:", out_file)

    # mapa combinado (centrar en promedio si hay datos)
    if not df_out.dropna(subset=["lat","lon"]).empty:
        center_lat = df_out["lat"].dropna().astype(float).mean()
        center_lon = df_out["lon"].dropna().astype(float).mean()
        crear_mapa(df_out, "mapa_librerias_combined.html", center=[center_lat, center_lon], zoom=7)

    # mapas por provincia
    for prov in PROVINCIAS:
        pn = normalizar(prov)
        sub = df_out[df_out["DESCRIPCION_PROVINCIA_EST"].apply(lambda x: normalizar(x)) == pn]
        if not sub.empty:
            center_lat = sub["lat"].dropna().astype(float).mean()
            center_lon = sub["lon"].dropna().astype(float).mean()
            fname = f"mapa_librerias_{pn.replace(' ','_')}.html"
            crear_mapa(sub, fname, center=[center_lat, center_lon], zoom=9)
        else:
            print("No hay datos georreferenciados para provincia:", prov)

    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
