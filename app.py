from flask import Flask, jsonify, render_template
import pandas as pd
import os

app = Flask(__name__)

DATA_FILE = os.path.join(
    'data', 'matched', 'places_enriched_with_sri.csv'
)

def safe(val):
    return None if pd.isna(val) else val

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/librerias")
def librerias():
    df = pd.read_csv("data/matched/places_enriched_with_sri.csv")

    def safe(v):
        return None if pd.isna(v) else v

    data = []
    for _, r in df.iterrows():
        if pd.isna(r.get("lat_places")) or pd.isna(r.get("lng_places")):
            continue

        data.append({
            "id": safe(r.get("place_id")),
            "nombre": safe(r.get("nombre_places")),
            "direccion": safe(r.get("direccion")),
            "provincia": safe(r.get("provincia")),
            "lat": float(r.get("lat_places")),
            "lng": float(r.get("lng_places")),
            "rating": float(r["rating"]) if not pd.isna(r.get("rating")) else 0,
            "web": safe(r.get("website")),
            "kw": safe(r.get("keyword_found")),
            "ruc": safe(r.get("NUMERO_RUC")),
            "razon_social": safe(r.get("RAZON_SOCIAL")),
            "match_type": safe(r.get("match_type")),
            "match_score": safe(r.get("match_score")),
        })

    return jsonify(data)

@app.route("/api/ventas-canton")
def ventas_por_canton():
    df = pd.read_csv(
        "data/cleaned/estimacion_ventas_librerias_por_canton.csv"
    )

    data = []
    for _, r in df.iterrows():
        data.append({
            "provincia": r["provincia"],
            "canton": r["canton"],
            "codigo_canton": str(r["codigo_canton"]),
            "numero_librerias": int(r["numero_librerias"]),
            "ventas_totales": float(r["ventas_totales"]) if not pd.isna(r["ventas_totales"]) else 0,
            "ventas_promedio": float(r["ventas_promedio"]) if not pd.isna(r["ventas_promedio"]) else 0,
        })

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
