import os
import json
import datetime
import numpy as np
import random
from util import load_json, store_json, count_sundays
# constraint_sample = {"id": "relation/6308508", "works":[0,4,7,12,13], "doesnt_work":[2,3,5,15]}
FOR_YEAR = 2025
MAX_WORKS = 14
sunday_count = count_sundays(FOR_YEAR)
MAX_DOESNT_WORK = sunday_count - MAX_WORKS

data = load_json("data/rawdata.json")

base = [i for i in range(sunday_count)]
constraints = {}

constraints["YEAR"] = FOR_YEAR
constraints["SUNDAYS"] = sunday_count
constraints["MAX_WORKS"] = MAX_WORKS
constraints["MAX_DOESNT_WORK"] = MAX_DOESNT_WORK

for id_ in data.keys():
    works = random.sample(base, random.randint(0, MAX_WORKS))
    doesnt_work = random.sample([i for i in base if i not in works], random.randint(0, MAX_DOESNT_WORK))
    constraints[id_] = {}
    constraints[id_]["works"] = works
    constraints[id_]["doesnt_work"] = doesnt_work


print(constraints)
store_json(constraints, "data/constraints.json")
