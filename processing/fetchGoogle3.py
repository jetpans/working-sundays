from myenv import API_KEY
from util import load_json, store_json
import requests
import os
import json
import time


longi, lati = (16.9665664, 46.1534122)
name, brand = ("", "")

req = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params={
    "location": f"{lati},{longi}",
    "radius": 20,
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
        print(details_resp["result"])
else:
    print("Didnt find")
