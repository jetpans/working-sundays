from algorithm.algorithms import optimize_cluster
from tools.generate_clusters import make_clusters
from constants import MAX_RADIUS_OF_INFLUENCE
from util import load_json, store_json, individual_to_json, haversine
from algorithm.models import FastIntersectUnionFitness, CrossoverGeometric, MutatorSimple, create_individual_based_on_others_heuristic1, CrossoverColumnGeometric, create_individual_random
import datetime
import os
import numpy as np
import random

OUTDIR = f'results/{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'
os.makedirs(OUTDIR, exist_ok=True)


if __name__ == "__main__":
    constraints = load_json("data/constraints.json")
    data = load_json("data/one_cluster_subset.json")
    JOIN_CLUSTER_AMOUNT = 3
    GENERATION_PLAN = [500, 30, 10] + [2]*20
    clusters = make_clusters(data, max_in_cluster=10, max_distance=MAX_RADIUS_OF_INFLUENCE)

    ctr = 0
    current_individuals = [None] * len(clusters)
    random_sol = create_individual_random(list(data.keys()), constraints, data)
    store_json(individual_to_json(random_sol), f"{OUTDIR}\\random_start.json")
    final_individuals = []
    while True:
        print(f"[META STEP] {ctr}")
        ctr += 1
        future_individuals = []
        store_json(clusters, f"{OUTDIR}\\metastep{ctr-1}_clusters.json")
        for index, cluster in enumerate(clusters):

            if len(cluster) == 1:  # Trivial case
                ind = create_individual_based_on_others_heuristic1(
                    cluster[::], constraints, data, current_individuals[index])
                future_individuals.append(ind)
                continue

            f_fitness = FastIntersectUnionFitness(cluster, constraints, data)
            crossover = CrossoverColumnGeometric(0.2)
            mutator = MutatorSimple(0.6, 2)
            settings = {
                "create_individual": lambda: create_individual_based_on_others_heuristic1(cluster[::], constraints, data, current_individuals[index]),
                "evaluate": lambda ind: f_fitness(ind),
                "mate": lambda ind1, ind2: crossover(ind1, ind2),
                "mutate": lambda ind: mutator(ind),
                "tournsize": 3,
                "clone": lambda ind: ind.copy(),
                "population_size": 50,
                "generations": GENERATION_PLAN[ctr-1],
                "crossover_probability": 0.7,
                "mutation_probability": 0.8,
                "elitism": 1,
            }

            p, best_individual = optimize_cluster(cluster, constraints, data, settings)
            store_json(individual_to_json(best_individual), f"{OUTDIR}\\metastep{ctr-1}_step{index}.json")
            print(f"Finished step {ctr-1}_{index}, best fitness: {best_individual.fitness}")
            future_individuals.append(best_individual)
        if len(clusters) == 1:
            final_individuals += future_individuals
            break
        new_clusters = []
        clusters_copy = clusters[::]
        while len(clusters_copy) > 0:
            random_one = random.choice(clusters_copy)
            distances = []
            for other in clusters_copy:
                mindist = 1e10
                minother = None
                for first_id in random_one:
                    for second_id in other:
                        lon1, lat1 = data[first_id]["coordinates"]
                        lon2, lat2 = data[second_id]["coordinates"]

                        dist = haversine(lat1, lon1, lat2, lon2)
                        if dist < mindist:
                            mindist = dist
                            minother = second_id
                distances.append((other, mindist))
            distances.sort(key=lambda x: x[1])
            distances = distances[:min(JOIN_CLUSTER_AMOUNT, len(distances))]
            if distances[1][1] > MAX_RADIUS_OF_INFLUENCE:
                clust = distances[0][0]
                clusters_copy.remove(clust)
                for ind in future_individuals:
                    for store_id in ind.cluster:
                        if store_id in clust:
                            final_individuals.append(ind)
                            break
                continue

            new_cluster = []
            for other, _ in distances:
                new_cluster += other
            new_clusters.append(new_cluster)
            for other, _ in distances:
                clusters_copy.remove(other)

        current_individuals = []
        for index, cluster in enumerate(new_clusters):
            current_individuals.append([])
            for other_ind in future_individuals:
                for store_id in other_ind.cluster:
                    if store_id in cluster:
                        current_individuals[index].append(other_ind)
                        break

        clusters = new_clusters

    giga_ind = create_individual_based_on_others_heuristic1(
        list(data.keys()), constraints, data, final_individuals)
    store_json(individual_to_json(giga_ind), f"{OUTDIR}\\metastep{ctr-1}_giga.json")
    store_json(giga_ind.cluster, f"{OUTDIR}\\giga_cluster.json")
    # Maybe don't join if distance is too big, maybe 2x max radius of influence GG
