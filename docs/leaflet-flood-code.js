// ============================================================================
// LEICESTER FLOOD RISK DATA - LEAFLET.JS CODE
// ============================================================================

let floodLayer;
fetch('leicester-flood-data.geojson')
  .then(response => response.json())
  .then(data => {
    floodLayer = L.geoJSON(data, {
      style: {
        color: 'darkblue',
        fillColor: '#0066cc',
        fillOpacity: 0.6,
        weight: 2
      },
      onEachFeature: function(feature, layer) {
        let popupContent = '<strong>Leicester Flood Risk</strong><br>';
        for (let key in feature.properties) {
          if (key !== 'geometry') {
            popupContent += key + ': ' + feature.properties[key] + '<br>';
          }
        }
        layer.bindPopup(popupContent);
      }
    });

    floodLayer.addTo(map);
    map.fitBounds(floodLayer.getBounds());
  })
  .catch(error => {
    console.error('Error loading flood data:', error);
  });

// ============================================================================
// SUMMARY DATA
// ============================================================================

const floodDataSummary = {
  "total_features": 990,
  "geometry_type": [
    "Point"
  ],
  "coordinate_system": "EPSG:4326",
  "bounding_box": {
    "min_x": -1.2059729073625218,
    "min_y": 52.58272416464982,
    "max_x": -1.0461926396364405,
    "max_y": 52.68728982632951
  },
  "clip_bbox_wgs84": {
    "min_x": -1.6075412373,
    "min_y": 52.3821710451,
    "max_x": -0.4183648815,
    "max_y": 52.9876790938
  },
  "columns": [
    "watercourse_ref_no",
    "watercourse_name",
    "structure",
    "type_of_structure",
    "location",
    "eastings",
    "northings",
    "geometry"
  ]
};

console.log('Total flood features:', floodDataSummary.total_features);
console.log('Bounding box:', floodDataSummary.bounding_box);
