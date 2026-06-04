#!/usr/bin/env python3
import argparse
import os
import json
import random
import sys
from datetime import datetime

# --- Configuration & Templates ---

MAP_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Vulnerability Map: {state}, {country}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        html, body, #map {{ height: 100%; width: 100%; margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        .nav-panel {{ position: absolute; top: 15px; left: 60px; z-index: 1000; display: flex; gap: 10px; }}
        .nav-button {{ background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
        .nav-button.secondary {{ background: #6c757d; }}
    </style>
</head>
<body>
<div class="nav-panel">
    <a href="../index.html" class="nav-button">🏠 Home</a>
    <a href="../deep_dive.html" class="nav-button secondary">📊 Deep Dive</a>
    <a href="results_charts.html" class="nav-button" style="background: #17a2b8;">📈 View Analysis Charts</a>
</div>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    const map = L.map('map').setView([{lat}, {lon}], {zoom});
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);

    const geojsonData = {geojson};
    L.geoJSON(geojsonData, {{
        style: function(feature) {{
            return {{ color: "#ff7800", weight: 2, opacity: 0.65, fillOpacity: 0.2 }};
        }}
    }}).addTo(map);

    // Simulated Data Points
    const points = {points};
    points.forEach(p => {{
        L.circleMarker([p.lat, p.lon], {{
            radius: p.size,
            fillColor: p.color,
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        }}).bindPopup(`<b>${{p.name}}</b><br>${{p.desc}}`).addTo(map);
    }});
</script>
</body>
</html>"""

CHARTS_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Analysis: {state}, {country}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .nav-panel {{ margin-bottom: 20px; display: flex; gap: 10px; }}
        .btn {{ padding: 10px 15px; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; background: #6c757d; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        canvas {{ max-height: 400px; }}
    </style>
</head>
<body>
<div class="container">
    <div class="nav-panel">
        <a href="../index.html" class="btn">🏠 Home</a>
        <a href="../deep_dive.html" class="btn">📊 Deep Dive</a>
        <a href="results_map.html" class="btn" style="background: #007bff;">🗺️ Back to Result Map</a>
    </div>
    <h1>📊 Vulnerability Analysis: {state}, {country}</h1>
    <p>Data Range: {start} - {end}</p>

    <div class="card">
        <h3>Conflict Events vs. Estimated Population Impact</h3>
        <canvas id="chart1"></canvas>
    </div>

    <div class="card">
        <h3>Risk Distribution by Sub-district</h3>
        <canvas id="chart2"></canvas>
    </div>
</div>
<script>
    new Chart(document.getElementById('chart1'), {{
        type: 'line',
        data: {{
            labels: {labels},
            datasets: [{{
                label: 'Conflict Events',
                data: {data1},
                borderColor: 'red',
                fill: false
            }}, {{
                label: 'Pop Risk Index',
                data: {data2},
                borderColor: 'blue',
                fill: false
            }}]
        }}
    }});

    new Chart(document.getElementById('chart2'), {{
        type: 'bar',
        data: {{
            labels: {sub_labels},
            datasets: [{{
                label: 'Vulnerability Score',
                data: {sub_data},
                backgroundColor: 'orange'
            }}]
        }}
    }});
</script>
</body>
</html>"""

def main():
    parser = argparse.ArgumentParser(description="Generate vulnerability analysis for a specific location.")
    parser.add_argument("--country", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--start", type=int, default=2020)
    parser.add_argument("--end", type=int, default=2024)
    args = parser.parse_args()

    print(f"--- Processing {args.state}, {args.country} ({args.start}-{args.end}) ---")

    # 1. Fetch Geodata (Mocking coordinates for portability without heavy dependencies)
    # In a real scenario, we'd use Nominatim or a GeoJSON service.
    # For this portable version, we generate a bounding box "center"
    lat, lon = 9.0820, 8.6753 # Default Nigeria center
    if "nigeria" not in args.country.lower():
        # Randomish center for other countries to show movement
        lat = random.uniform(-20, 40)
        lon = random.uniform(-20, 50)
    
    # Simple Mock GeoJSON (A square around the center)
    offset = 1.0
    mock_geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": args.state},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon-offset, lat-offset], [lon+offset, lat-offset],
                    [lon+offset, lat+offset], [lon-offset, lat+offset],
                    [lon-offset, lat-offset]
                ]]
            }
        }]
    }

    # 2. Simulated Points (Schools, IDP sites, Conflict)
    points = []
    for i in range(15):
        p_lat = lat + random.uniform(-0.8, 0.8)
        p_lon = lon + random.uniform(-0.8, 0.8)
        type_choice = random.choice(["School", "IDP Site", "Conflict"])
        if type_choice == "School":
            color, name, size = "green", f"School {i}", 5
        elif type_choice == "IDP Site":
            color, name, size = "blue", f"IDP Camp {i}", 8
        else:
            color, name, size = "red", f"Attack {i}", 6
        
        points.append({
            "lat": p_lat, "lon": p_lon, "color": color, 
            "name": name, "size": size, "desc": f"Status: Active | Risk: Medium"
        })

    # 3. Chart Data Generation
    years = list(range(args.start, args.end + 1))
    data1 = [random.randint(10, 100) for _ in years]
    data2 = [random.randint(20, 80) for _ in years]
    sub_labels = [f"District {i}" for i in range(1, 6)]
    sub_data = [random.uniform(0.1, 0.9) for _ in range(5)]

    # 4. Save Artifacts
    os.makedirs("More", exist_ok=True)
    
    map_html = MAP_TEMPLATE.format(
        state=args.state, country=args.country, lat=lat, lon=lon, zoom=7,
        geojson=json.dumps(mock_geojson), points=json.dumps(points)
    )
    with open("More/results_map.html", "w") as f:
        f.write(map_html)

    charts_html = CHARTS_TEMPLATE.format(
        state=args.state, country=args.country, start=args.start, end=args.end,
        labels=json.dumps(years), data1=json.dumps(data1), data2=json.dumps(data2),
        sub_labels=json.dumps(sub_labels), sub_data=json.dumps(sub_data)
    )
    with open("More/results_charts.html", "w") as f:
        f.write(charts_html)

    print(f"Success! Generated:")
    print(f" - More/results_map.html")
    print(f" - More/results_charts.html")

if __name__ == "__main__":
    main()
