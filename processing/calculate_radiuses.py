import json
import math
import sys
import argparse
import os
from util import haversine


# ================= CONFIGURATION =================
# 1. MAX_RADIUS: How far a huge store (e.g. 1500+ ratings) draws people
#    if it is completely alone in the middle of nowhere.
MAX_THEORETICAL_RADIUS_KM = 5.0

# 2. MIN_RADIUS: The smallest area a store is allowed to cover,
#    even if it's tiny and surrounded by 50 competitors.
MIN_RADIUS_KM = 0.5

# 3. SENSITIVITY: How "scared" a store is of competition.
#    0.05 = Moderate drop-off (Standard Gravity Model)
#    0.20 = High drop-off (Stores shrink aggressively if neighbors exist)
COMPETITION_SENSITIVITY = 0.08
# =================================================


def process_stores(data):
    # Convert Dict to List for iteration, keeping track of IDs
    store_ids = list(data.keys())
    stores = [data[k] for k in store_ids]

    # 1. Sanitize Data & Find Max
    max_ratings = 0
    for s in stores:
        # Default to 10 ratings if missing
        if 'user_ratings_total' not in s or s['user_ratings_total'] is None:
            s['user_ratings_total'] = 10

        if s['user_ratings_total'] > max_ratings:
            max_ratings = s['user_ratings_total']

    if max_ratings == 0:
        max_ratings = 1.0

    print(f"[*] Analyzing {len(stores)} stores.")
    print(f"[*] Max Rating found: {max_ratings} (Standard for 100% radius)")

    # 2. Calculate Radius
    for i, current in enumerate(stores):
        # Format is usually [Lon, Lat] in GeoJSON-like structures
        curr_lon = current['coordinates'][0]
        curr_lat = current['coordinates'][1]

        # --- A. BASE CALCULATION (Size) ---
        # Square root allows area to scale linearly with popularity
        size_ratio = current['user_ratings_total'] / max_ratings
        base_radius = math.sqrt(size_ratio) * MAX_THEORETICAL_RADIUS_KM

        # --- B. GRAVITY MODEL (Competition) ---
        pressure_sum = 0.0

        for j, other in enumerate(stores):
            if i == j:
                continue  # Skip self

            other_lon = other['coordinates'][0]
            other_lat = other['coordinates'][1]

            dist = haversine(curr_lat, curr_lon, other_lat, other_lon)

            # Avoid division by zero for duplicates/errors
            if dist < 0.02:
                dist = 0.02

            # The Gravity Formula: Mass / Distance^2
            # Bigger neighbors exert more pressure.
            # Neighbors further away exert exponentially less pressure.
            other_mass = other['user_ratings_total'] / max_ratings
            pressure = other_mass / (dist ** 2)

            pressure_sum += pressure

        # --- C. DECAY FUNCTION ---
        # Radius = Base / (1 + (Sensitivity * Pressure))
        decay_factor = 1.0 + (COMPETITION_SENSITIVITY * pressure_sum)
        final_radius = base_radius / decay_factor

        # --- D. CLAMPING ---
        if final_radius < MIN_RADIUS_KM:
            final_radius = MIN_RADIUS_KM

        # Update the dictionary object in place
        current['radius_km'] = round(final_radius, 4)

    # 3. Re-map list back to original dictionary structure
    result = {}
    for i, k in enumerate(store_ids):
        result[k] = stores[i]

    return result


def main():
    parser = argparse.ArgumentParser(description="Calculate density-based store radii.")
    parser.add_argument("input_file", help="Path to input JSON file")
    parser.add_argument("-o", "--output", help="Path to output JSON file (default: suffix with _radii)")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found.")
        sys.exit(1)

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        sys.exit(1)

    # Process
    enriched_data = process_stores(data)

    # Determine output path
    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input_file)
        out_path = f"{base}_radii{ext}"

    # Write
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, indent=4, ensure_ascii=False)
        print(f"[+] Success! Saved to: {out_path}")
    except Exception as e:
        print(f"Error writing file: {e}")


if __name__ == "__main__":
    main()
