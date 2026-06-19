#!/usr/bin/env python3
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "docs"
OUT_DIR = DOCS_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Leicester Flood Risk Dashboard</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    #map { height: 620px; width: 100%; border-radius: 8px; }
    .layer-toggle { display:inline-block; margin:5px; padding:8px 16px; border:none; border-radius:4px; cursor:pointer; font-weight:600; }
    .layer-toggle.active { opacity:1; box-shadow:0 0 0 3px rgba(0,0,0,.2); }
    .stat-card { background:white; border-radius:8px; padding:16px; box-shadow:0 2px 4px rgba(0,0,0,.1); }
    .stat-value { font-size:2em; font-weight:bold; color:#0066cc; }
    .popup-content { font-size:14px; max-width:300px; }
    .popup-section { margin:8px 0; padding:8px; background:#f0f9ff; border-radius:4px; }
    .popup-label { font-weight:bold; color:#333; }
    .popup-value { color:#666; }
  </style>
</head>
<body class="bg-gray-100">
  <header class="bg-blue-600 text-white p-6">
    <div class="max-w-6xl mx-auto">
      <h1 class="text-3xl font-bold">Leicester Flood Risk Dashboard</h1>
      <p class="mt-2 text-blue-100">Interactive map showing flood risk structures, historic events, and EA flood zones</p>
    </div>
  </header>
  <main class="max-w-6xl mx-auto p-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div class="stat-card"><div class="stat-value">990</div><div class="stat-label">Flood Defense Structures</div></div>
      <div class="stat-card"><div class="stat-value text-red-600">127</div><div class="stat-label">Historic Flood Events</div></div>
      <div class="stat-card"><div class="stat-value">668</div><div class="stat-label">EA Flood Zones</div></div>
    </div>
    <div class="bg-white p-4 rounded-lg mb-6 shadow">
      <h2 class="text-lg font-bold mb-3">Toggle Data Layers</h2>
      <div class="flex flex-wrap">__BUTTONS__</div>
    </div>
    <div id="map"></div>
  </main>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const map = L.map('map');
    const bounds = [[52.58272416464982, -1.2059729073625218],[52.68728982632951, -1.0461926396364405]];
    map.fitBounds(bounds);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors', maxZoom: 19 }).addTo(map);
    const addPopup = (feature, layer, title) => {
      const props = feature.properties || {};
      let c = `<div class="popup-content"><strong>${title}</strong>`;
      Object.entries(props).forEach(([k, v]) => { if (v !== null && v !== undefined && k.toLowerCase() !== 'geometry') c += `<div class="popup-section"><span class="popup-label">${k}</span><br><span class="popup-value">${v}</span></div>`; });
      c += `</div>`; layer.bindPopup(c);
    };
    let leicesterLayer = null, historicLayer = null, eaLayer = null;
    function toggleLayer(name) { const layer = name === 'leicester' ? leicesterLayer : name === 'historic' ? historicLayer : eaLayer; const btn = document.getElementById(`toggle-${name}`); if (!layer) return; if (map.hasLayer(layer)) { map.removeLayer(layer); btn.classList.remove('active'); btn.classList.add('bg-gray-400'); } else { layer.addTo(map); btn.classList.add('active'); btn.classList.remove('bg-gray-400'); } }
"""

TEMPLATE_TAIL = """
  </script>
</body>
</html>
"""

def buttons(kind):
    if kind == "leicester":
        return '<button id="toggle-leicester" onclick="toggleLayer(\'leicester\')" class="layer-toggle active bg-blue-600 text-white">Leicester Flood Structures</button>'
    if kind == "historic":
        return '<button id="toggle-historic" onclick="toggleLayer(\'historic\')" class="layer-toggle active bg-red-600 text-white">Historic Flood Events</button>'
    if kind == "ea":
        return '<button id="toggle-ea-flood" onclick="toggleLayer(\'ea-flood\')" class="layer-toggle active bg-indigo-600 text-white">EA Flood Zones</button>'
    return """<button id="toggle-leicester" onclick="toggleLayer('leicester')" class="layer-toggle active bg-blue-600 text-white">Leicester Flood Structures</button>
    <button id="toggle-historic" onclick="toggleLayer('historic')" class="layer-toggle active bg-red-600 text-white">Historic Flood Events</button>
    <button id="toggle-ea-flood" onclick="toggleLayer('ea-flood')" class="layer-toggle active bg-indigo-600 text-white">EA Flood Zones</button>"""

def js_leicester():
    return """
    fetch('leicester-flood-data.geojson').then(r => r.json()).then(data => {
      leicesterLayer = L.geoJSON(data, {
        pointToLayer: (f, ll) => L.circleMarker(ll, { radius: 5, color: 'darkblue', fillColor: '#0066cc', fillOpacity: 0.7, weight: 2 }),
        onEachFeature: (feature, layer) => addPopup(feature, layer, 'Leicester Flood Structure')
      }).addTo(map);
    }).catch(console.error);
"""

def js_historic():
    return """
    fetch('historic-flood-data.geojson').then(r => r.json()).then(data => {
      historicLayer = L.geoJSON(data, {
        style: { color: '#8b0000', fillColor: '#ff0000', fillOpacity: 0.3, weight: 2 },
        onEachFeature: (feature, layer) => addPopup(feature, layer, 'Historic Flood Event')
      }).addTo(map);
    }).catch(console.error);
"""

def js_ea():
    return """
    fetch('ea-flood-zones.geojson').then(r => r.json()).then(data => {
      eaLayer = L.geoJSON(data, {
        style: (feature) => {
          const p = feature.properties || {};
          const z = String(p.flood_zone || p.Flood_Zone || p.zone || p.Zone || '');
          if (z === '2') return { color: '#0066cc', fillColor: '#66b3ff', fillOpacity: 0.45, weight: 2 };
          if (z === '3') return { color: '#003366', fillColor: '#0066cc', fillOpacity: 0.55, weight: 2 };
          return { color: '#999', fillColor: '#ccc', fillOpacity: 0.35, weight: 1 };
        },
        onEachFeature: (feature, layer) => addPopup(feature, layer, 'EA Flood Zone')
      }).addTo(map);
    }).catch(console.error);
"""

files = {
    "map-leicester-structures.html": (buttons("leicester"), js_leicester()),
    "map-historic-events.html": (buttons("historic"), js_historic()),
    "map-ea-flood-zones.html": (buttons("ea"), js_ea()),
    "map-combined-all-layers.html": (buttons("all"), js_leicester() + js_historic() + js_ea()),
}

for filename, (btns, body_js) in files.items():
    html = TEMPLATE_HEAD.replace("__BUTTONS__", btns) + body_js + TEMPLATE_TAIL
    (OUT_DIR / filename).write_text(html, encoding="utf-8")

print("Wrote:")
for filename in files:
    print("-", OUT_DIR / filename)
