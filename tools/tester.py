from algorithm.algorithms import optimize_cluster
from tools.generate_clusters import make_clusters
from constants import MAX_RADIUS_OF_INFLUENCE
from util import load_json, store_json, individual_to_json, haversine
from algorithm.models import FastIntersectUnionFitness
import datetime
import os
import numpy as np
import random
from util import load_individual_from_json


def test():
    constraints = load_json("data/constraints.json")
    data = load_json("data/rawdata.json")

    ind1 = load_individual_from_json("results\\2025-05-05_20-28-13\\random_start.json")
    ind2 = load_individual_from_json("results\\2025-05-05_20-28-13\\metastep2_giga.json")

    ind3 = load_individual_from_json("results\\2025-05-09_15-52-42\\random_start.json")
    ind4 = load_individual_from_json("results\\2025-05-09_15-52-42\\metastep0_step0.json")

    fitness = FastIntersectUnionFitness()
    f1 = fitness(ind1)
    f2 = fitness(ind2)
    f3 = fitness(ind3)
    f4 = fitness(ind4)

    print(f3, f4)
    print(f1, f2)


test()
