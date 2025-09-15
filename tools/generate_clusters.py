import os
import json
from util import load_json, store_json, haversine
import random


def make_clusters(data, max_in_cluster=5, max_distance=3):
    clusters = []
    data = data.copy()
    while len(data) > 0:
        cluster = []
        cluster.append(list(data.keys())[random.randint(0, len(data) - 1)])

        while len(cluster) < max_in_cluster and len(data) > 0:
            # find closest store to cluster
            closest = None
            closest_distance = float("inf")
            for dude in cluster:
                for other in data.keys():
                    if dude == other or other in cluster:
                        continue
                    distance = haversine(data[dude]["coordinates"][1], data[dude]["coordinates"][0],
                                         data[other]["coordinates"][1], data[other]["coordinates"][0])
                    if distance < closest_distance:
                        closest_distance = distance
                        closest = other
            if closest_distance < max_distance:
                cluster.append(closest)
            else:
                break
        print(data[cluster[0]]["formatted_address"])
        print(cluster)
        clusters.append(cluster)
        for dude in cluster:
            del data[dude]
    return clusters


if __name__ == "__main__":
    data = load_json("data/rawdata.json")
    clusters = make_clusters(data, max_in_cluster=10, max_distance=4)

    store_json(clusters, "data/clusters.json")
