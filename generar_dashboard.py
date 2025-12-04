import pandas as pd
import json
import os

# ================= CONFIGURACIÓN DE RUTAS =================
# Basado en la estructura que me diste
INPUT_FILE = os.path.join('cleaned', 'librerias_georef_all.csv')
OUTPUT_FILE = os.path.join('outputs', 'mapa_librerias_dashboard_final.html')

def cargar_y_procesar_datos():
    print(f"📂 Leyendo archivo: {INPUT_FILE}...")
    
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print("❌ Error: No se encuentra el archivo CSV. Verifica la ruta.")
        return None

    # Lista para almacenar los objetos procesados
    data_list = []

    print("⚙️  Procesando datos y limpiando valores nulos...")
    
    for _, row in df.iterrows():
        # Limpieza de Rating: Si es NaN o vacío, poner 0
        rating = 0.0
        try:
            val = row.get('rating', 0)
            rating = float(val) if pd.notna(val) and val != '' else 0.0
        except:
            rating = 0.0

        # Limpieza de Web: Si es NaN, dejar string vacío
        web = row.get('website', '')
        if pd.isna(web): web = ""

        # Construir el objeto JSON requerido por el mapa
        item = {
            "id": str(row.get('place_id', '')),
            "nombre": str(row.get('nombre', 'Sin nombre')),
            "direccion": str(row.get('direccion', 'Sin dirección')),
            "provincia": str(row.get('provincia', 'Desconocida')),
            "lat": float(row.get('lat', 0)),
            "lng": float(row.get('lng', 0)),
            "rating": rating,
            "web": web,
            "kw": str(row.get('keyword_found', ''))
        }
        data_list.append(item)
    
    # Convertir a string JSON para inyectar en JS
    return json.dumps(data_list, ensure_ascii=False)

# ================= PLANTILLA HTML =================
# Esta es la interfaz moderna con filtros que diseñé para ti
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Librerías - Ecuador</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.3/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster/dist/MarkerCluster.Default.css" />
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"/>
    <style>
        body { margin: 0; padding: 0; font-family: 'Roboto', sans-serif; }
        #map { height: 100vh; width: 100%; z-index: 1; }
        .control-panel {
            position: absolute; top: 20px; left: 20px; width: 300px;
            background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px);
            padding: 20px; border-radius: 12px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            z-index: 1000; transition: all 0.3s ease;
            max-height: 90vh; overflow-y: auto;
        }
        .control-panel h2 { margin-top: 0; font-size: 1.2rem; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .filter-group { margin-bottom: 15px; }
        label { display: block; font-size: 0.85rem; color: #555; margin-bottom: 5px; font-weight: 500; }
        select, input[type="text"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        input[type="range"] { width: 100%; }
        .stats { background: #f1f8ff; color: #2980b9; padding: 10px; border-radius: 6px; font-size: 0.85rem; text-align: center; font-weight: bold; margin-top: 15px; }
        .toggle-btn { display: none; position: absolute; top: 10px; left: 10px; z-index: 1001; background: white; border: none; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        @media (max-width: 768px) { .control-panel { left: -320px; } .control-panel.active { left: 0; } .toggle-btn { display: block; } }
        /* Popup Styles */
        .custom-popup .leaflet-popup-content-wrapper { border-radius: 8px; padding: 0; overflow: hidden; }
        .custom-popup .leaflet-popup-content { margin: 0; width: 280px !important;}
        .popup-header { background: #3498db; color: white; padding: 10px 15px; font-weight: bold; }
        .popup-body { padding: 15px; font-size: 0.9rem; }
        .popup-rating { display: inline-block; background: #f1c40f; color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; margin-bottom: 8px; }
        .btn-link { display: block; text-align: center; background: #2ecc71; color: white; text-decoration: none; padding: 8px; border-radius: 4px; margin-top: 10px; }
        .btn-link:hover { background: #27ae60; }
    </style>
</head>
<body>
    <button class="toggle-btn" onclick="togglePanel()"><i class="fas fa-filter"></i> Filtros</button>
    <div class="control-panel" id="panel">
        <h2><i class="fas fa-map-marked-alt"></i> Explorador</h2>
        <div class="filter-group">
            <label>Buscar (Nombre/Palabra Clave)</label>
            <input type="text" id="searchFilter" placeholder="Ej: Papelería, Éxito..." oninput="filterData()">
        </div>
        <div class="filter-group">
            <label>Provincia</label>
            <select id="provinceFilter" onchange="filterData()">
                <option value="all">Todas las Provincias</option>
            </select>
        </div>
        <div class="filter-group">
            <label>Rating Mínimo: <span id="ratingVal">0</span> <i class="fas fa-star" style="color:#f1c40f"></i></label>
            <input type="range" id="ratingFilter" min="0" max="5" step="0.1" value="0" oninput="filterData()">
        </div>
        <div class="stats" id="statsCounter">Cargando datos...</div>
    </div>
    <div id="map"></div>
    <script src="https://unpkg.com/leaflet@1.9.3/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster/dist/leaflet.markercluster.js"></script>
    <script>
        // --- INYECCIÓN DE DATOS DESDE PYTHON ---
        const rawData = [DATA_PLACEHOLDER]; 

        var map = L.map('map').setView([-1.8312, -78.1834], 7); // Centro aprox Ecuador
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
        var markersCluster = L.markerClusterGroup();
        map.addLayer(markersCluster);

        function initProvinceFilter() {
            const provinces = [...new Set(rawData.map(item => item.provincia))].sort();
            const select = document.getElementById('provinceFilter');
            provinces.forEach(prov => {
                let option = document.createElement("option");
                option.value = prov; option.text = prov; select.appendChild(option);
            });
        }

        function filterData() {
            const text = document.getElementById('searchFilter').value.toLowerCase();
            const province = document.getElementById('provinceFilter').value;
            const minRating = parseFloat(document.getElementById('ratingFilter').value);
            document.getElementById('ratingVal').innerText = minRating;
            markersCluster.clearLayers();
            let count = 0;
            rawData.forEach(item => {
                const nombre = item.nombre ? item.nombre.toLowerCase() : "";
                const kw = item.kw ? item.kw.toLowerCase() : "";
                const matchText = (nombre.includes(text) || kw.includes(text));
                const matchProv = (province === 'all' || item.provincia === province);
                const matchRating = (item.rating >= minRating);
                if (matchText && matchProv && matchRating) { createMarker(item); count++; }
            });
            document.getElementById('statsCounter').innerText = `Mostrando ${count} de ${rawData.length} resultados`;
        }

        function createMarker(item) {
            let color = '#3498db';
            if(item.rating >= 4.5) color = '#2ecc71';
            else if(item.rating > 0 && item.rating < 3.5) color = '#e74c3c';
            
            var marker = L.circleMarker([item.lat, item.lng], {
                radius: 8, fillColor: color, color: "#fff", weight: 2, opacity: 1, fillOpacity: 0.8
            });
            const popupContent = `
                <div class="popup-header">${item.nombre}</div>
                <div class="popup-body">
                    ${item.rating > 0 ? `<div class="popup-rating"><i class="fas fa-star"></i> ${item.rating}</div>` : ''}
                    <p><i class="fas fa-map-marker-alt"></i> ${item.direccion}</p>
                    <p><i class="fas fa-city"></i> ${item.provincia}</p>
                    ${item.web ? `<a href="${item.web}" target="_blank" class="btn-link">Visitar Sitio Web</a>` : ''}
                </div>`;
            marker.bindPopup(popupContent, { className: 'custom-popup' });
            markersCluster.addLayer(marker);
        }

        initProvinceFilter();
        filterData();
    </script>
</body>
</html>
"""

def generar_html():
    json_data = cargar_y_procesar_datos()
    if json_data:
        # Reemplazar el marcador DATA_PLACEHOLDER con los datos reales
        html_content = HTML_TEMPLATE.replace('[DATA_PLACEHOLDER]', json_data)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ ¡Éxito! Archivo generado en: {OUTPUT_FILE}")
        print("   Abre este archivo en tu navegador para ver el mapa con todos los datos.")

if __name__ == "__main__":
    generar_html()