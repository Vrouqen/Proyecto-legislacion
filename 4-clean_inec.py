import pandas as pd
from pathlib import Path

# =========================
# 0. Rutas
# =========================
RAW_PATH = "data/raw/EMPRESAS_periodo_2024.csv"
CLEAN_DIR = Path("data/cleaned")
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# 1. Leer CSV INEC
# =========================
df = pd.read_csv(
    RAW_PATH,
    sep=";",
    encoding="utf-16",
    dtype=str,
    low_memory=False
)

print("✔ Archivo cargado")
print("Columnas:", len(df.columns))

# =========================
# 2. Normalizar provincia y cantón
# =========================
df["provincia"] = (
    df["provincia"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df["canton"] = (
    df["canton"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# =========================
# 3. Filtrar provincias de estudio
# =========================
PROVINCIAS_VALIDAS = ["MORONA SANTIAGO", "TUNGURAHUA"]
df = df[df["provincia"].isin(PROVINCIAS_VALIDAS)]

print("✔ Provincias filtradas:", PROVINCIAS_VALIDAS)
print("Registros restantes:", df.shape[0])

# =========================
# 4. Limpiar columnas de ventas
# =========================
VENTAS_COLS = [
    "ventas_totales",
    "ventas_nacionales",
    "ventas_rimpe",
    "ventas_totales_rimpe"
]

for col in VENTAS_COLS:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

# =========================
# 5. Seleccionar columnas relevantes
# =========================
COLUMNAS_FINALES = [
    "id_empresa",
    "anio",
    "provincia",
    "codigo_provincia",
    "canton",
    "codigo_canton",
    "seccion",
    "codigo_division",
    "codigo_clase",
    "clase",
    "ventas_totales",
    "ventas_nacionales",
    "ventas_rimpe",
    "ventas_totales_rimpe",
    "estrato_ventas",
    "tamanoe_empleo",
    "tamanoe_plazas"
]

COLUMNAS_FINALES = [c for c in COLUMNAS_FINALES if c in df.columns]
df = df[COLUMNAS_FINALES]

# =========================
# 6. Filtrar librerías (CIIU G4761)
# =========================
CODIGO_LIBRERIAS = "G4761"

df_librerias = df[
    df["codigo_clase"].str.strip().str.upper() == CODIGO_LIBRERIAS
].copy()

print("✔ Librerías identificadas:", df_librerias.shape[0])

# =========================
# 7. Guardar dataset limpio de librerías
# =========================
df_librerias.to_csv(
    CLEAN_DIR / "inec_librerias_morona_tungurahua.csv",
    index=False,
    encoding="utf-8"
)

# =========================
# 8. Estimación de ventas por librería (análisis geográfico)
# =========================
ventas_geo = (
    df_librerias
    .groupby(
        ["provincia", "codigo_provincia", "canton", "codigo_canton"],
        as_index=False
    )
    .agg(
        numero_librerias=("id_empresa", "count"),
        ventas_totales=("ventas_totales", "sum"),
        ventas_promedio=("ventas_totales", "mean"),
        ventas_mediana=("ventas_totales", "median")
    )
)

# =========================
# 9. Guardar dataset geográfico
# =========================
ventas_geo.to_csv(
    CLEAN_DIR / "estimacion_ventas_librerias_por_canton.csv",
    index=False,
    encoding="utf-8"
)

# =========================
# 10. Resumen final
# =========================
print("\n✔ Proceso finalizado correctamente")
print("Librerías totales:", ventas_geo["numero_librerias"].sum())
print("Cantones analizados:", ventas_geo.shape[0])
print("Provincias:", ventas_geo["provincia"].unique())
