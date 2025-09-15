
import json
import os
from util import load_json, store_json
from myenv import API_KEY


# import util

# {
#       "type": "Feature",
#       "properties": {
#         "@id": "way/661348355",
#         "addr:city": "Funtana",
#         "addr:country": "HR",
#         "addr:housenumber": "1P",
#         "addr:postcode": "52452",
#         "addr:street": "Dalmatinska",
#         "brand": "Plodine",
#         "brand:wikidata": "Q58040098",
#         "building": "yes",
#         "contact:email": "plodine@plodine.hr",
#         "contact:phone": "+385 52 866 080",
#         "contact:website": "https://www.plodine.hr",
#         "name": "Plodine",
#         "opening_hours": "Mo-Su 07:00-22:00",
#         "shop": "supermarket",
#         "@geometry": "center"
#       },
#       "geometry": {
#         "type": "Point",
#         "coordinates": [
#           13.6078308,
#           45.1768807
#         ]
#       },
#       "id": "way/661348355"
#     },

DATA_URL = "data/geodata.geojson"
data = load_json(DATA_URL)
connect = load_json("data/connect.json")

rawdata = {}

for element in data["features"]:
    id_ = element["properties"]["@id"]
    if id_ not in connect:
        continue
    connect_data = connect[id_]
    geo_data = element["properties"]
    coordinates = element["geometry"]["coordinates"]

    properties = {
        "name": connect_data["name"],
        "brand": geo_data.get("brand", ""),
        "rating": connect_data["rating"],
        "user_ratings_total": connect_data["user_ratings_total"],
        "formatted_address": connect_data["formatted_address"],
        "coordinates": coordinates
    }
    rawdata[id_] = properties
store_json(rawdata, "data/rawdata.json")
