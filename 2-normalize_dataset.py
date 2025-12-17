"""
normalize_datasets.py
Normaliza nombres comerciales de:
- Librerías SRI georreferenciadas
- Librerías Google Places

Salida:
- CSV normalizados listos para matching
"""

import os
import re
import unicodedata
import pandas as pd

# ---------------- CONFIG ----------------
DATA_DIR = "data"
OUT_DIR = os.path.join(DATA_DIR, "normalized")

SRI_FILE = os.path.join(DATA_DIR, "cleaned/librerias_georef_all.csv")
PLACES_FILE = os.path.join(DATA_DIR, "scrapped/librerias_ecuador_tungurahua_morona_intermedia.csv")

# ----------------------------------------

STOPWORDS = {
    # rubro
    "LIBRERIA", "LIBRERÍA",
    "PAPELERIA", "PAPELERÍA",

    # genéricas comerciales
    "COMERCIAL", "ALMACEN", "ALMACÉN",
    "DISTRIBUIDORA", "DISTRIBUIDOR",

    # ruido detectado en datos reales
    "FERIA", "LIBRO", "LIBROS",
    "ARTE", "ARTES",
    "SU",

    # conectores
    "Y", "DE", "DEL", "LA", "EL", "LOS", "LAS"
}

def ensure_dirs():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

def quitar_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

def normalizar_nombre(texto):
    if pd.isna(texto) or not str(texto).strip():
        return ""

    texto = str(texto).upper()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

    # solo letras
    texto = re.sub(r"[^A-Z\s]", " ", texto)

    tokens = []
    for t in texto.split():
        if t in STOPWORDS or len(t) <= 2:
            continue
        t = normalizar_token(t)
        tokens.append(t)

    return " ".join(tokens)

def normalizar_token(token: str) -> str:
    # plural simple → singular
    if token.endswith("ES") and len(token) > 4:
        return token[:-2]
    if token.endswith("S") and len(token) > 4:
        return token[:-1]
    return token


# ---------------- MAIN ----------------
def main():
    ensure_dirs()

    # ---------- SRI ----------
    print("Leyendo SRI:", SRI_FILE)
    sri = pd.read_csv(SRI_FILE, dtype=str)

    if "nombre" not in sri.columns:
        raise ValueError("El CSV del SRI debe tener la columna 'nombre'")

    sri["nombre_norm"] = sri["nombre"].apply(normalizar_nombre)

    sri_out = os.path.join(OUT_DIR, "sri_normalized.csv")
    sri.to_csv(sri_out, index=False, encoding="utf-8")
    print("SRI normalizado:", sri_out)

    # ---------- PLACES ----------
    print("Leyendo Places:", PLACES_FILE)
    places = pd.read_csv(PLACES_FILE, dtype=str)

    if "nombre" not in places.columns:
        raise ValueError("El CSV de Places debe tener la columna 'nombre'")

    places["nombre_norm"] = places["nombre"].apply(normalizar_nombre)

    places_out = os.path.join(OUT_DIR, "places_normalized.csv")
    places.to_csv(places_out, index=False, encoding="utf-8")
    print("Places normalizado:", places_out)

    print("Normalización finalizada correctamente.")

if __name__ == "__main__":
    main()
