from myenv import API_KEY
from util import load_json, store_json
import requests
import os
import json
import time


# https://maps.googleapis.com/maps/api/place/nearbysearch/json
#   ?location=45.815399,15.966568
#   &radius=100
#   &keyword=supermarket|convenience_store|grocery_or_supermarket
#   &key=YOUR_API_KEY

# https://maps.googleapis.com/maps/api/place/textsearch/json?
# query=Spar%2C+Ulica+Ivana+Banjavčića+22a%2C+Zagreb+10000
# &location=45.8095893%2C16.0011734
# &radius=100
# &key=YOUR_API_KEY


# https://maps.googleapis.com/maps/api/place/details/json?
# place_id=PASTE_PLACE_ID_HERE
# &fields=name,formatted_address,user_ratings_total,rating
# &key=YOUR_API_KEY

# {'type': 'Feature', 'properties': {'@id': 'relation/6308508', 'addr:city': 'Zagreb', 'addr:housenumber': '22a', 'addr:postcode': '10000', 'addr:street': 'Ulica Ivana Banjavčića', 'brand': 'Spar',
# 'brand:wikidata': 'Q610492', 'brand:wikipedia': 'en:SPAR (retailer)', 'building': 'yes', 'name': 'Spar', 'shop': 'supermarket', 'type': 'multipolygon', '@geometry': 'center'}, 'geometry': {'type': 'Point', 'coordinates': [16.0011734, 45.8095893]}, 'id': 'relation/6308508'}

DATA_URL = "data/geodata.geojson"
data = load_json(DATA_URL)
connections = load_json("data/connect.json")

connection_map = {}
ctr = 0
for element in data["features"]:
    longi, lati = element["geometry"]["coordinates"]

    props = element["properties"]
    _id = props["@id"]

    if _id in connections and "rating" in connections[_id].keys():
        continue

    name = element['properties'].get('name', '')
    brand = element['properties'].get('brand', '')

    req = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params={
        "location": f"{lati},{longi}",
        "radius": 10,
        "keyword": f"supermarket|convenience_store|grocery_or_supermarket|{name}|{brand}|trgovina|grocery",
        "key": API_KEY
    })
    resp = req.json()
    if resp["results"]:
        place_id = resp["results"][0]["place_id"]
        details_req = requests.get("https://maps.googleapis.com/maps/api/place/details/json",
                                   params={
                                       "place_id": place_id,
                                       "fields": "name,formatted_address,user_ratings_total,rating",
                                       "key": API_KEY
                                   })
        details_resp = details_req.json()
        print("DETAILS RESPONSE IS: ", details_resp)
        if details_resp["result"]:
            connection_map[_id] = details_resp["result"]
        else:
            connection_map[_id] = {}
    else:
        element["properties"]["details"] = {}
    store_json(connection_map, "data/connect_map.json")
