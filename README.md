# Análisis de Mercado de Librerías y Papelerías en Ecuador 🇪🇨
### (Enfoque: Tungurahua y Morona Santiago)

Este proyecto es una herramienta integral de **Inteligencia de Negocios (BI)** diseñada para mapear, analizar y estimar las ventas del sector de librerías, papelerías y suministros de oficina. El sistema combina técnicas de *web scraping*, procesamiento de datos gubernamentales abiertos y algoritmos de coincidencia (matching) para generar un dashboard interactivo.

## 📋 Descripción del Proyecto

El objetivo es consolidar una base de datos georreferenciada y enriquecida económicamente para entender la distribución y el tamaño de mercado de las librerías en provincias específicas.

El flujo de trabajo abarca:
1.  **Extracción:** Scraping de Google Maps Places API.
2.  **Normalización:** Limpieza de texto para cruce de datos.
3.  **Enriquecimiento:** Cruce con bases de datos del SRI (RUCs activos).
4.  **Estimación:** Proyección de ventas basada en encuestas del INEC.
5.  **Visualización:** Dashboard web interactivo.

## 🗄️ Fuentes de Datos

El proyecto se alimenta de tres fuentes principales y una descartada:

### 1. Google Places API (Scraping)
Se extrajo la ubicación, nombre, rating y dirección de establecimientos.
* **Estrategia:** Búsqueda por grilla (Centro, Noreste, Suroeste) para maximizar la cobertura en Tungurahua y Morona Santiago.
* **Keywords:** `librería`, `papelería`, `útiles escolares`, `textos escolares`, `suministros de oficina`, etc.

### 2. Servicio de Rentas Internas (SRI)
Se utilizó el Catastro Tributario para validar la existencia legal de los negocios y obtener datos fiscales.
* **Fuente:** [Datos Abiertos SRI](https://www.sri.gob.ec/datasets)
* **Uso:** Validación de RUC y actividad económica.

### 3. INEC (Directorio de Empresas)
Utilizado para la estimación de ventas promedio por provincia y categoría.
* **Fuente:** [Directorio de Empresas INEC](https://www.ecuadorencifras.gob.ec/directoriodeempresas/)
* **Uso:** Asignación de rangos de venta a los negocios identificados.

### 4. Superintendencia de Compañías (Descartada) ⚠️
Se intentó obtener el Estado de Pérdidas y Ganancias (P&L) desde el [Portal de Ranking](https://appscvsmovil.supercias.gob.ec/ranking/reporte.html).
* **Razón de exclusión:** La información se presenta en un dashboard de PowerBI difícil de scrapear, los datos solo llegan hasta 2024 y, lo más crítico, **menos del 5%** de las empresas extraídas del SRI cruzaban con esta base de datos (la mayoría son personas naturales o PYMES no registradas en la Supercias).

## 📂 Estructura del Proyecto

```text
├── data/
│   ├── raw/           # Datos crudos del SRI y CSVs iniciales
│   ├── scrapped/      # Resultados JSON/CSV del script de Google Places
│   ├── normalized/    # Datos con nombres estandarizados para matching
│   ├── matched/       # Dataset final enriquecido (Places + SRI)
│   └── cleaned/       # Datos finales listos para el dashboard (con ventas INEC)
├── datos_shp/         # Shapefiles (Provincias, Cantones) para mapas
├── static/            # Archivos CSS/JS para la web
├── templates/         # Plantillas HTML (dashboard.html)
├── 1-process_librerias_SRI.py  # Procesa y limpia datos crudos del SRI
├── 2-normalize_dataset.py      # Estandarización de textos (fuzzy matching prep)
├── 3-match_datasets.py         # Algoritmo de cruce (Google Places vs SRI)
├── 4-clean_inec.py             # Procesamiento y estimación de ventas INEC
├── app.py                      # Servidor Flask para el Dashboard
└── README.md
```

## ⚙️ Instalación y Uso
Prerrequisitos
Python 3.8+

Google Maps API Key (Places API habilitado)

**1.  Configuración del Entorno**
Clona el repositorio e instala las dependencias:
pip install flask pandas requests geopandas googlemaps

**2. Ejecución del Pipeline de Datos**
Si deseas regenerar la data desde cero, ejecuta los scripts en orden numérico:

Procesar SRI: python 1-process_librerias_SRI.py

Normalizar: python 2-normalize_dataset.py

Cruzar (Match): python 3-match_datasets.py

Estimaciones INEC: python 4-clean_inec.py

**3. Ejecutar el Web Scraper (Opcional)**
El script de scraping se encuentra documentado dentro del repositorio. Requiere una API Key válida.

Configuración: Radio de búsqueda de 60km con offsets de coordenadas (0.0, 0.3, -0.3) para cubrir áreas amplias.

**4. Levantar el Dashboard**
Para visualizar los mapas y estadísticas:

python app.py

Accede a http://localhost:5000 en tu navegador.

## 🧠 Metodología de Matching

El reto principal fue cruzar nombres comerciales informales (Google Maps) con razones sociales formales (SRI).

Limpieza: Eliminación de sufijos legales (S.A., Cía. Ltda.) y caracteres especiales.

Geocodificación Inversa: Validación de que el negocio del SRI pertenezca a la misma provincia/cantón que el punto de Google.

Fuzzy Matching: Se utiliza similitud de texto para encontrar el candidato más probable en la base del SRI para cada punto de Google Maps.

## 📊 Visualización

El dashboard (dashboard.html) utiliza los datos procesados y los shapefiles de datos_shp para renderizar:

Mapa de calor de densidad de librerías.

Estimación de ventas por cantón.

Distribución de competidores en Tungurahua y Morona Santiago.