import folium
from folium.plugins import Fullscreen
from util import load_json, store_json, radius_of_influence_from_solution
from geopy.distance import distance
import json
import sys

CLUSTERING = sys.argv[1]
INFILE = sys.argv[2]
OUTFILE = sys.argv[3]
# Load data
data = load_json("data/rawdata.json")
clustering = load_json(CLUSTERING)
solution = load_json(INFILE)
l = list(data.keys())[::]
for key in l:
    if key not in solution:
        del data[key]

# Hard-coded distinct colors
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

# Add fullscreen control
Fullscreen().add_to(m)

# Create a feature group for each Sunday (only one will be visible at a time)
sunday_groups = []
for sunday in range(55):
    sunday_group = folium.FeatureGroup(name=f"Sunday {sunday+1}", show=False)
    sunday_groups.append(sunday_group)

# Add store markers to the map (always visible)
for store_id, store_info in data.items():
    # Extract information
    name = store_info.get('name', 'No Name')
    coordinates = store_info.get('coordinates', [0, 0])
    class_id = store_info.get('class_id', -1)

    # Add standard markers for all stores (always visible on the map)
    if class_id != -1 and class_id < len(DISTINCT_COLORS):
        color = DISTINCT_COLORS[class_id]

        # Add circle marker for all stores (like in the original code)
        folium.CircleMarker(
            location=[coordinates[1], coordinates[0]],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(f"<b>{name}</b><br>Store ID: {store_id}<br>Class ID: {class_id}", max_width=300),
            tooltip=f"Class {class_id}"
        ).add_to(m)

# Add influence areas for each Sunday
for sunday in range(55):
    # For each store in the solution for this Sunday
    for store_id, sundays_list in solution.items():
        # Skip if store not in data
        if store_id not in data:
            continue

        # Check if this store is working on this Sunday
        if sunday in sundays_list:
            store_info = data[store_id]
            coordinates = store_info.get('coordinates', [0, 0])
            class_id = store_info.get('class_id', -1)

            # Skip if no class assigned
            if class_id == -1:
                continue

            # Get the cluster for this store
            cluster = None
            for c in clustering:
                if store_id in c:
                    cluster = c
                    break

            if not cluster:
                continue

            # Calculate radius of influence using the new function
            radius_km = radius_of_influence_from_solution(store_id, cluster, data, solution, sunday)
            radius_m = radius_km * 1000  # Convert to meters

            # Get coordinates
            lat, lon = coordinates[1], coordinates[0]

            # Create square for influence area (like in the original code)
            half_side_m = radius_m / 2  # Half the side length in meters

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

            # Draw square in the layer for this Sunday
            folium.Polygon(
                locations=square_coords,
                color=DISTINCT_COLORS[class_id],
                fill=True,
                fill_color=DISTINCT_COLORS[class_id],
                fill_opacity=0.2,
                popup=f"Store: {store_info.get('name', 'Unknown')}<br>Radius: {radius_km:.2f} km"
            ).add_to(sunday_groups[sunday])

# Add all Sunday layers to the map (but they'll be hidden initially)
for sunday_group in sunday_groups:
    sunday_group.add_to(m)

# Add a legend for the clusters
legend_html = '''
<div style="position: fixed; 
     bottom: 50px; left: 50px; width: 170px; height: auto; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; padding: 10px;
     ">
     <b>Class Legend</b><br>
'''

class_id_count = {}
for store_info in data.values():
    class_id = store_info.get('class_id', -1)
    if class_id not in class_id_count:
        class_id_count[class_id] = 0
    class_id_count[class_id] += 1

for class_id in sorted(class_id_count.keys()):
    if class_id != -1 and class_id < len(DISTINCT_COLORS):
        color = DISTINCT_COLORS[class_id]
        count = class_id_count[class_id]
        legend_html += f'<i style="background:{color};width:10px;height:10px;display:inline-block;"></i> Class {class_id} ({count} stores)<br>'

legend_html += '</div>'
m.get_root().html.add_child(folium.Element(legend_html))

# Add improved Sunday selector control
sunday_selector_js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        try {
            // Create the Sunday selector control
            var SundayControl = L.Control.extend({
                options: {
                    position: 'topright'
                },
                
                onAdd: function(map) {
                    var container = L.DomUtil.create('div', 'sunday-selector leaflet-bar leaflet-control');
                    container.style.backgroundColor = 'white';
                    container.style.padding = '10px';
                    container.style.border = '2px solid rgba(0,0,0,0.2)';
                    container.style.borderRadius = '4px';
                    container.style.boxShadow = '0 1px 5px rgba(0,0,0,0.4)';
                    
                    var title = L.DomUtil.create('div', '', container);
                    title.innerHTML = 'Sunday Influence';
                    title.style.fontWeight = 'bold';
                    title.style.marginBottom = '8px';
                    title.style.textAlign = 'center';
                    title.style.borderBottom = '1px solid #ccc';
                    title.style.paddingBottom = '5px';
                    
                    var label = L.DomUtil.create('label', '', container);
                    label.innerHTML = 'Select Sunday: ';
                    label.style.fontWeight = 'bold';
                    label.style.marginRight = '5px';
                    label.style.display = 'block';
                    label.style.marginBottom = '5px';
                    
                    var selector = L.DomUtil.create('select', '', container);
                    selector.id = 'sunday-select';
                    selector.style.width = '100%';
                    selector.style.padding = '4px';
                    selector.style.borderRadius = '3px';
                    selector.style.border = '1px solid #ccc';
                    
                    for (var i = 1; i <= 55; i++) {
                        var option = L.DomUtil.create('option', '', selector);
                        option.value = i - 1;  // 0-based index
                        option.text = 'Sunday ' + i;
                    }
                    
                    var info = L.DomUtil.create('div', '', container);
                    info.id = 'sunday-info';
                    info.style.fontSize = '11px';
                    info.style.marginTop = '8px';
                    info.style.color = '#666';
                    info.innerHTML = 'Viewing Sunday 1';
                    
                    L.DomEvent.on(selector, 'change', function() {
                        var sunday = parseInt(this.value);
                        updateVisibleSunday(sunday);
                        document.getElementById('sunday-info').innerHTML = 'Viewing Sunday ' + (sunday + 1);
                    });
                    
                    L.DomEvent.disableClickPropagation(container);
                    return container;
                }
            });
            
            // Function to update which Sunday is visible
            function updateVisibleSunday(sundayIndex) {
                // Get all layer controls
                var layerControls = document.querySelectorAll('.leaflet-control-layers-selector');
                
                // Hide all Sunday layers first
                for (var i = 0; i < layerControls.length; i++) {
                    var label = layerControls[i].nextSibling;
                    if (label && label.textContent && label.textContent.trim().startsWith('Sunday ')) {
                        if (layerControls[i].checked) {
                            layerControls[i].click();  // Uncheck/hide this layer
                        }
                    }
                }
                
                // Show only the selected Sunday layer
                for (var i = 0; i < layerControls.length; i++) {
                    var label = layerControls[i].nextSibling;
                    if (label && label.textContent && label.textContent.trim() === 'Sunday ' + (sundayIndex + 1)) {
                        if (!layerControls[i].checked) {
                            layerControls[i].click();  // Check/show this layer
                        }
                        break;
                    }
                }
            }
            
            // Get the map instance
            var maps = document.querySelectorAll('.folium-map');
            if (maps.length > 0) {
                var map = maps[0]._leaflet_map;
                if (map) {
                    // Add our custom control
                    new SundayControl().addTo(map);
                    
                    // Initialize with Sunday 1 visible
                    setTimeout(function() {
                        updateVisibleSunday(0);
                    }, 1000);
                }
            }
        } catch (e) {
            console.error("Error adding Sunday selector control:", e);
        }
    }, 1000); // Wait for map to initialize
});
</script>
"""

m.get_root().html.add_child(folium.Element(sunday_selector_js))

# Add Layer Control
folium.LayerControl().add_to(m)

# Save the map
m.save(f"results/{OUTFILE}.html")
print("Map has been created and saved as 'croatia_sunday_influence_map.html'")
