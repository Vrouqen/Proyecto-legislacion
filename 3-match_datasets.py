"""
match_datasets.py
Places es el dataset principal.
SRI solo enriquece si hay coincidencia.
"""

import os
import pandas as pd
from difflib import SequenceMatcher

# ---------------- CONFIG ----------------
DATA_DIR = "data/normalized"
OUT_DIR = "data/matched"

PLACES_FILE = os.path.join(DATA_DIR, "places_normalized.csv")
SRI_FILE = os.path.join(DATA_DIR, "sri_normalized.csv")

SCORE_MIN = 0.85
# ---------------------------------------

def ensure_dirs():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def main():
    ensure_dirs()

    places = pd.read_csv(PLACES_FILE, dtype=str)
    sri = pd.read_csv(SRI_FILE, dtype=str)

    # limpiar nombre_norm vacío
    places["nombre_norm"] = places["nombre_norm"].fillna("")
    sri["nombre_norm"] = sri["nombre_norm"].fillna("")

    results = []

    for _, p in places.iterrows():
        best_match = None
        best_score = 0
        match_type = None

        candidatos = sri[
            (sri["nombre_norm"] != "") &
            (sri["DESCRIPCION_PROVINCIA_EST"].str.upper() == p["provincia"].upper())
        ]

        # ---------- MATCH EXACTO ----------
        exact = candidatos[candidatos["nombre_norm"] == p["nombre_norm"]]
        if not exact.empty:
            best_match = exact.iloc[0]
            best_score = 1.0
            match_type = "exact"
        else:
            # ---------- FUZZY ----------
            for _, s in candidatos.iterrows():
                score = similarity(p["nombre_norm"], s["nombre_norm"])
                if score > best_score and score >= SCORE_MIN:
                    best_match = s
                    best_score = score
                    match_type = "fuzzy"

        # ---------- CONSTRUIR FILA ----------
        row = {
            # ----- PLACES (siempre) -----
            "place_id": p["place_id"],
            "nombre_places": p["nombre"],
            "direccion": p.get("direccion"),
            "provincia": p.get("provincia"),
            "lat_places": p.get("lat"),
            "lng_places": p.get("lng"),
            "rating": p.get("rating"),
            "website": p.get("website"),
            "keyword_found": p.get("keyword_found"),

            # ----- MATCH INFO -----
            "match_type": match_type,
            "match_score": round(best_score, 3) if best_match is not None else None,

            # ----- SRI (opcional) -----
            "NUMERO_RUC": None,
            "RAZON_SOCIAL": None,
            "nombre_sri": None,
            "CODIGO_CIIU": None,
            "DESCRIPCION_CANTON_EST": None,
            "DESCRIPCION_PARROQUIA_EST": None,
            "lat_sri": None,
            "lon_sri": None,
        }

        if best_match is not None:
            row.update({
                "NUMERO_RUC": best_match.get("NUMERO_RUC"),
                "RAZON_SOCIAL": best_match.get("RAZON_SOCIAL"),
                "nombre_sri": best_match.get("nombre"),
                "CODIGO_CIIU": best_match.get("CODIGO_CIIU"),
                "DESCRIPCION_CANTON_EST": best_match.get("DESCRIPCION_CANTON_EST"),
                "DESCRIPCION_PARROQUIA_EST": best_match.get("DESCRIPCION_PARROQUIA_EST"),
                "lat_sri": best_match.get("lat"),
                "lon_sri": best_match.get("lon"),
            })

        results.append(row)

    df_out = pd.DataFrame(results)

    out_file = os.path.join(OUT_DIR, "places_enriched_with_sri.csv")
    df_out.to_csv(out_file, index=False, encoding="utf-8")

    print("Proceso finalizado.")
    print("Total Places:", len(df_out))
    print("Con match SRI:", df_out["NUMERO_RUC"].notna().sum())
    print("Sin match SRI:", df_out["NUMERO_RUC"].isna().sum())
    print("Archivo:", out_file)

if __name__ == "__main__":
    main()
