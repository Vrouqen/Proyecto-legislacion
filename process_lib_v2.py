"""
process_librerias.py (versión v2 desde JSON)
Lee un JSON con puntos de librerías (Tungurahua / Morona Santiago)
y genera:
- CSV limpio con todos los puntos
- Mapas HTML (combinado y por provincia) con MarkerCluster.
"""

import os
import json
import pandas as pd
import folium
from folium.plugins import MarkerCluster

# --- Config ---
JSON_PATH = "cleaned/librerias_ecuador_tungurahua_morona_intermedia.json"  # ajusta la ruta si hace falta
CLEAN_DIR = "cleaned"
OUT_DIR = "outputs"

PROVINCIAS = ["MORONA SANTIAGO", "TUNGURAHUA"]   # provincias a considerar (en mayúsculas)

# Salidas
OUT_CSV_ALL = os.path.join(CLEAN_DIR, "librerias_georef_all.csv")  # puedes cambiar el nombre si quieres
import pandas as pd  # ya lo tienes

def sanitize(text):
    """Limpia texto para que no rompa el JS de folium."""
    if pd.isna(text):
        return ""
    s = str(text)
    # Evitar secuencias tipo \1, \2, etc. que rompen template strings
    s = s.replace("\\", "/")
    # Por si acaso, evitar backticks (`)
    s = s.replace("`", "'")
    return s


def ensure_dirs():
    for d in (CLEAN_DIR, OUT_DIR):
        if d and not os.path.exists(d):
            os.makedirs(d)

def main():
    ensure_dirs()

    # 1) Leer JSON
    if not os.path.exists(JSON_PATH):
        raise SystemExit(f"No se encontró el JSON: {JSON_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SystemExit("El JSON no es una lista de objetos. Revisa el formato.")

    df = pd.DataFrame(data)
    print(f"Registros totales en JSON: {len(df)}")

    # Asegurar columnas esperadas
    expected_cols = {"place_id", "nombre", "direccion", "provincia", "lat", "lng", "rating", "website", "keyword_found"}
    missing = expected_cols - set(df.columns)
    if missing:
        print("Advertencia: faltan columnas en el JSON:", missing)

    # 2) Filtrar por provincias de interés
    df["prov_norm"] = df["provincia"].astype(str).str.strip().str.upper()
    df = df[df["prov_norm"].isin(PROVINCIAS)].copy()
    print("Registros tras filtrar provincias:", len(df))

    if df.empty:
        print("No hay registros para las provincias configuradas. Revisa el JSON o la lista PROVINCIAS.")
        return

    # 3) Limpiar y guardar CSV
    cols_out = [
        "place_id",
        "nombre",
        "direccion",
        "provincia",
        "lat",
        "lng",
        "rating",
        "website",
        "keyword_found",
    ]
    # Solo las columnas que existan realmente
    cols_out = [c for c in cols_out if c in df.columns]

    df_out = df[cols_out].copy()
    df_out.to_csv(OUT_CSV_ALL, index=False, encoding="utf-8")
    print("CSV combinado guardado en:", OUT_CSV_ALL)

    # 4) Función para crear mapas (usa lat/lng del JSON)
    def crear_mapa(df_map, fname, center=None, zoom=8):
        df_map = df_map.dropna(subset=["lat", "lng"])
        if df_map.empty:
            print("No hay coordenadas válidas para el mapa:", fname)
            return

        # Centro por defecto: promedio de los puntos si no se pasa center
        if center is None:
            center_lat = df_map["lat"].astype(float).mean()
            center_lng = df_map["lng"].astype(float).mean()
            center = [center_lat, center_lng]

        m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")
        marker_cluster = MarkerCluster().add_to(m)

        for _, r in df_map.iterrows():
            nombre = sanitize(r.get("nombre", "Sin nombre"))
            direccion = sanitize(r.get("direccion", "Sin dirección"))
            provincia = sanitize(r.get("provincia", "Sin provincia"))
            rating = r.get("rating", None)
            keyword = sanitize(r.get("keyword_found", ""))

            rating_txt = f"Rating: {rating}" if pd.notna(rating) else "Rating: N/D"
            keyword_txt = f"Keyword: {keyword}" if keyword else ""

            popup_html = (
                f"<b>{nombre}</b><br>"
                f"{direccion}<br>"
                f"Provincia: {provincia}<br>"
                f"{rating_txt}<br>"
                f"{keyword_txt}"
            )

            popup = folium.Popup(popup_html, max_width=300)

            folium.CircleMarker(
                location=[float(r["lat"]), float(r["lng"])],
                radius=5,
                color="blue",
                fill=True,
                fill_color="cyan",
                fill_opacity=0.9,
                popup=popup,
            ).add_to(marker_cluster)

        out_file = os.path.join(OUT_DIR, fname)
        m.save(out_file)
        print("Mapa guardado:", out_file)

    # 5) Mapa combinado (nombre con _v2)
    crear_mapa(df_out, "mapa_librerias_combined_v2.html", zoom=7)

    # 6) Mapas por provincia (nombres con _v2)
    for prov in PROVINCIAS:
        sub = df_out[df_out["provincia"].astype(str).str.strip().str.upper() == prov]
        if not sub.empty:
            fname = f"mapa_librerias_{prov.replace(' ', '_')}_v2.html"
            crear_mapa(sub, fname, zoom=9)
        else:
            print("No hay datos para provincia:", prov)

    print("Proceso finalizado (v2 desde JSON).")

if __name__ == "__main__":
    main()
