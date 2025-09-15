import folium
from util import load_json, store_json, radius_of_influence
from geopy.distance import distance
import sys
# Outfilename from args
OUTFILE = sys.argv[2]
INFILE = sys.argv[1]
data = load_json("data/rawdata.json")
clustering = load_json(INFILE)

# Hard-coded distinct colors instead of generating them
DISTINCT_COLORS = [
    '#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
    '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4',
    '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000',
    '#aaffc3', '#808000', '#ffd8b1', '#000075', '#a9a9a9'
]

# Ensure we have enough colors
while len(DISTINCT_COLORS) < len(clustering):
    DISTINCT_COLORS.extend(DISTINCT_COLORS)

# Assign class IDs to each store based on clustering
for store_id, store_info in data.items():
    # Default class
    store_info['class_id'] = -1

    # Assign based on clustering
    for cluster_id, cluster in enumerate(clustering):
        if store_id in cluster:
            store_info['class_id'] = cluster_id
            break

# Create a map centered around Croatia
croatia_coords = [45.1, 16.0]
m = folium.Map(location=croatia_coords, zoom_start=8)

# Debug information
class_id_count = {}

# Create a feature group for polygons that can be toggled
polygon_group = folium.FeatureGroup(name="Influence Areas")

# Add markers for each store
for store_id, store_info in data.items():
    # Extract information
    name = store_info.get('name', 'No Name')
    coordinates = store_info.get('coordinates', [0, 0])
    class_id = store_info.get('class_id', -1)

    # Count class IDs for debugging
    if class_id not in class_id_count:
        class_id_count[class_id] = 0
    class_id_count[class_id] += 1

    # Add appropriate markers
    if class_id != -1 and class_id < len(DISTINCT_COLORS):
        color = DISTINCT_COLORS[class_id]

        # Add circle marker
        folium.CircleMarker(
            location=[coordinates[1], coordinates[0]],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(f"<b>{name}</b><br>Class ID: {class_id}", max_width=300),
            tooltip=f"Class {class_id}"
        ).add_to(m)

        # Calculate and add the influence area polygon to the polygon group
        lat, lon = coordinates[1], coordinates[0]
        half_side_m = radius_of_influence(store_id, clustering[class_id], data) * 1000 / 2  # Convert km to m

        north = distance(meters=half_side_m).destination((lat, lon), 0)
        east = distance(meters=half_side_m).destination((lat, lon), 90)
        south = distance(meters=half_side_m).destination((lat, lon), 180)
        west = distance(meters=half_side_m).destination((lat, lon), 270)

        # Define square using corners (SW, SE, NE, NW, back to SW)
        square_coords = [
            (south.latitude, west.longitude),
            (south.latitude, east.longitude),
            (north.latitude, east.longitude),
            (north.latitude, west.longitude),
            (south.latitude, west.longitude)  # Close the loop
        ]

        # Draw square in the polygon group
        folium.Polygon(
            locations=square_coords,
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.2
        ).add_to(polygon_group)

# Add the polygon feature group to the map
polygon_group.add_to(m)

# Add a legend
legend_html = '''
<div style="position: fixed; 
     bottom: 50px; left: 50px; width: 170px; height: auto; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; padding: 10px;
     ">
     <b>Class Legend</b><br>
'''

for class_id in sorted(class_id_count.keys()):
    if class_id != -1 and class_id < len(DISTINCT_COLORS):
        color = DISTINCT_COLORS[class_id]
        count = class_id_count[class_id]
        legend_html += f'<i style="background:{color};width:10px;height:10px;display:inline-block;"></i> Class {class_id} ({count} stores)<br>'

legend_html += '</div>'

# Instead of using a JavaScript toggle, use Folium's built-in LayerControl
folium.LayerControl().add_to(m)

# Add a simple button that uses a different approach to toggle the polygon group
toggle_js = """
<script>
// Add a custom control button for toggling polygons
var polygonToggleControl = L.Control.extend({
    options: {
        position: 'topright'
    },
    
    onAdd: function(map) {
        // Create a container for our control
        var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
        
        // Create the toggle button
        var button = L.DomUtil.create('a', '', container);
        button.href = '#';
        button.title = 'Toggle Polygons';
        button.innerHTML = 'Hide Polygons';
        button.style.width = 'auto';
        button.style.padding = '0 8px';
        button.style.textDecoration = 'none';
        button.style.fontWeight = 'bold';
        button.style.fontSize = '12px';
        button.style.lineHeight = '28px';
        button.style.color = '#555';
        button.style.background = 'white';
        
        // Store the polygon group name
        this._polygonGroupName = 'Influence Areas';
        this._polygonsVisible = true;
        this._button = button;
        
        // Add event listener
        L.DomEvent.on(button, 'click', this._togglePolygons, this);
        L.DomEvent.disableClickPropagation(container);
        
        return container;
    },
    
    _togglePolygons: function(e) {
        L.DomEvent.preventDefault(e);
        
        // Get all layer controls and find our polygon group
        var layerControls = document.querySelectorAll('.leaflet-control-layers-selector');
        
        for (var i = 0; i < layerControls.length; i++) {
            var label = layerControls[i].nextSibling;
            if (label && label.textContent && label.textContent.trim() === this._polygonGroupName) {
                // Found our layer checkbox - click it to toggle
                layerControls[i].click();
                
                // Update button text
                this._polygonsVisible = !this._polygonsVisible;
                this._button.innerHTML = this._polygonsVisible ? 'Hide Polygons' : 'Show Polygons';
                break;
            }
        }
    }
});

// Add the control to the map
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        try {
            // Get the Leaflet map instance
            var maps = document.querySelectorAll('.folium-map');
            if (maps.length > 0) {
                var map = maps[0]._leaflet_map;
                if (map) {
                    new polygonToggleControl().addTo(map);
                }
            }
        } catch (e) {
            console.error("Error adding polygon toggle control:", e);
        }
    }, 1000); // Give the map time to initialize
});
</script>
"""

m.get_root().html.add_child(folium.Element(toggle_js))

# Print debug info
print(f"Number of clusters: {len(clustering)}")
print(f"Class distribution: {class_id_count}")
print(f"First few colors: {DISTINCT_COLORS[:5]}")

# Save the map

m.save(f"results/{OUTFILE}.html")
print("Map has been created and saved as 'croatia_stores_map.html'")
