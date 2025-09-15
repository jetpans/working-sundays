import os
import json
import datetime
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
from constants import MAX_RADIUS_OF_INFLUENCE


def load_json(file_path):
    """Load a JSON file and return its content as a dictionary."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding="utf-8") as file:
        data = json.load(file)

    return data


def store_json(data, file_path):
    """Store a dictionary as a JSON file."""
    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def count_sundays(year):
    sundays = 0
    for month in range(1, 13):
        for day in range(1, 32):
            try:
                date = datetime.date(year, month, day)
                if date.weekday() == 6:  # Sunday
                    sundays += 1
            except ValueError:
                continue
    return sundays


def generate_n_colors(n):
    """Generate n visually distinct colors and return as hex color codes."""
    # Predefined list of distinct colors for better visibility
    base_colors = [
        "#e6194B", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
        "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4",
        "#469990", "#dcbeff", "#9A6324", "#fffac8", "#800000",
        "#aaffc3", "#808000", "#ffd8b1", "#000075", "#a9a9a9"
    ]

    # If we need more colors than in our predefined list
    if n > len(base_colors):
        # Create additional colors using HSV color space for maximum distinction
        import colorsys

        # Start with our base colors
        result = base_colors.copy()

        # Generate additional colors
        additional_needed = n - len(base_colors)
        for i in range(additional_needed):
            # Evenly spaced hues, full saturation and value
            h = (i / additional_needed)
            s = 0.9  # High saturation
            v = 0.9  # High value/brightness

            # Convert to RGB
            r, g, b = colorsys.hsv_to_rgb(h, s, v)

            # Convert to hex
            hex_color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
            result.append(hex_color)

        return result
    else:
        # If we have enough predefined colors, just use those
        return base_colors[:n]


def radius_of_influence(store_id, cluster, data):
    """Calculate the radius of influence for a store based on its reviews."""
    # Get the coordinates of the store
    total_population = data[store_id]["user_ratings_total"]
    my_population = data[store_id]["user_ratings_total"]
    for other_id in cluster:
        if other_id == store_id:
            continue
        total_population += data[other_id]["user_ratings_total"]

    return sqrt(my_population / total_population) * MAX_RADIUS_OF_INFLUENCE  # kilometers


def radius_of_influence_from_solution(store_id, cluster, data, solution, sunday):
    total_population = 1e-10
    my_population = 0
    for other_id in cluster:
        if sunday in solution[other_id]:
            total_population += data[other_id]["user_ratings_total"]
            if store_id == other_id:
                my_population = data[other_id]["user_ratings_total"]
    return sqrt(my_population / total_population) * MAX_RADIUS_OF_INFLUENCE  # kilometers


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance_km = R * c
    return distance_km


def latlon_to_xy(lat, lon, lat0=45.10000, lon0=15.2000):
    """Convert latitude and longitude to x, y coordinates."""
    R = 6371.0  # Earth radius in kilometers
    x = R * np.radians(lon - lon0) * np.cos(np.radians(lat0))
    y = R * np.radians(lat - lat0)
    return x, y


def fast_latlon_to_xy(lat, lon, lat0=45.10000, lon0=15.2000):
    lat = np.radians(lat)
    lon = np.radians(lon)
    lat0 = np.radians(lat0)
    lon0 = np.radians(lon0)
    R = 6371.0  # Earth radius in kilometers
    x = R * (lon - lon0) * np.cos(lat0)
    y = R * (lat - lat0)
    return x, y


def create_box(lon, lat, radius):
    x, y = latlon_to_xy(lat, lon)
    return box(x - radius, y - radius, x + radius, y + radius)


def fast_create_boxes(coords, radii):
    lons, lats = zip(*coords)
    x, y = fast_latlon_to_xy(np.array(lats), np.array(lons))

    r = radii

    res = np.array([x - r, y - r, x + r, y + r]).T

    return res  # [x_min, y_min, x_max, y_max]


def union_intersect(boxes):
    """Calculate the total overlapping area of a list of boxes."""

    union = unary_union(boxes) if boxes else None

    intersects = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            intersection = boxes[i].intersection(boxes[j])
            if not intersection.is_empty:
                intersects.append(intersection)
    intersect = unary_union(intersects) if intersects else None
    return (union.area if union else 0, intersect.area if intersect else 0)


def fast_union_intersect(boxes):
    """
    Calculate the total union and intersection area of a list of boxes using a sweep line algorithm.
    Matches the output of the original Shapely implementation with algebraic accuracy.

    Args:
        boxes: numpy array of shape (n, 4) where each row is [x1, y1, x2, y2]

    Returns:
        tuple: (union_area, intersect_area)
    """
    if len(boxes) == 0:
        return 0.0, 0.0

    # First, calculate all pairwise intersections
    intersections = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            box1 = boxes[i]
            box2 = boxes[j]

            # Calculate intersection coordinates
            x1 = max(box1[0], box2[0])
            y1 = max(box1[1], box2[1])
            x2 = min(box1[2], box2[2])
            y2 = min(box1[3], box2[3])

            # Check if intersection exists
            if x2 > x1 and y2 > y1:
                # Store intersection box
                intersections.append([x1, y1, x2, y2])

    # Create a list of all rectangles (original boxes and their intersections)
    all_rects = []
    for box in boxes:
        all_rects.append(("box", box))

    for inter in intersections:
        all_rects.append(("intersection", np.array(inter)))

    # If no intersections, just sum the box areas for union
    if not intersections:
        box_areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        union_area = np.sum(box_areas)
        return union_area, 0.0

    # Function to calculate area using inclusion-exclusion principle
    def calculate_areas():
        # 1. Calculate area of each original box
        box_areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        total_box_area = np.sum(box_areas)

        # 2. Calculate area of each intersection
        intersection_areas = np.array([(box[2] - box[0]) * (box[3] - box[1]) for box in intersections])
        total_intersection_area = np.sum(intersection_areas)

        # 3. Calculate area of overlaps between intersections (for inclusion-exclusion)
        # This is where we need to handle multiple overlapping regions carefully

        # Create all unique x and y coordinates for a segment tree / sweep line
        x_coords = set()
        y_coords = set()

        for box in boxes:
            x_coords.add(box[0])
            x_coords.add(box[2])
            y_coords.add(box[1])
            y_coords.add(box[3])

        x_coords = sorted(list(x_coords))
        y_coords = sorted(list(y_coords))

        # Map coordinates to indices
        x_map = {coord: i for i, coord in enumerate(x_coords)}
        y_map = {coord: i for i, coord in enumerate(y_coords)}

        # Create a 2D grid to track overlap counts
        width = len(x_coords)
        height = len(y_coords)
        grid = np.zeros((height, width), dtype=int)

        # Fill the grid with box overlaps
        for box in boxes:
            x1_idx = x_map[box[0]]
            y1_idx = y_map[box[1]]
            x2_idx = x_map[box[2]]
            y2_idx = y_map[box[3]]

            # Mark grid cells covered by this box
            for y in range(y1_idx, y2_idx):
                for x in range(x1_idx, x2_idx):
                    grid[y, x] += 1

        # Calculate exact areas using the grid and actual coordinates
        union_area = 0
        intersect_area = 0

        for y in range(height - 1):
            for x in range(width - 1):
                cell_count = grid[y, x]
                if cell_count > 0:
                    # Calculate exact cell area
                    cell_width = x_coords[x + 1] - x_coords[x]
                    cell_height = y_coords[y + 1] - y_coords[y]
                    cell_area = cell_width * cell_height

                    # Add to union area
                    union_area += cell_area

                    # Add to intersection area if covered by 2+ boxes
                    if cell_count >= 2:
                        intersect_area += cell_area

        return union_area, intersect_area

    # Calculate results with algebraic precision
    union_area, intersect_area = calculate_areas()
    return union_area, intersect_area


def individual_to_json(ind):
    sol = {}
    for i, id_ in enumerate(ind.cluster):
        sol[id_] = ind.works[i] + ind.model[i]
        sol[id_] = list(map(int, sol[id_]))
    return sol


def load_individual_from_json(file_path):
    from algorithm.models import MyIndividual
    constraints = load_json("data/constraints.json")
    data = load_json("data/rawdata.json")
    with open(file_path, 'r', encoding="utf-8") as file:
        ind = json.load(file)
        cluster = list(ind.keys())
        works = [ind[id_] for id_ in cluster]

        new_ind = MyIndividual(cluster, constraints, data)
        new_ind.works = works
        new_ind.model = [0] * len(cluster)
        new_ind.big_matrix = np.zeros((len(cluster), constraints["SUNDAYS"]))
        for index, row in enumerate(works):
            for item in row:
                new_ind.big_matrix[index][item] = data[cluster[index]]["user_ratings_total"]
    return new_ind
