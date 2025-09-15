from util import load_json, store_json
import os
import json

print("Cook")
connections = load_json("data/connect.json")
for id_ in connections.keys():
    if "rating" not in connections[id_].keys():
        connections[id_]["rating"] = 3.5
    if "user_ratings_total" not in connections[id_].keys():
        connections[id_]["user_ratings_total"] = 1
# store_json(connections, "data/newone.json")
