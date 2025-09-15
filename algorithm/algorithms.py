import random
from deap import base, creator, tools
from algorithm.models import IntersectUnionFitness, MyIndividual, \
    create_individual_random, CrossoverGeometric, MutatorSimple, create_individual_heuristic1, FastIntersectUnionFitness
from util import load_json, store_json, individual_to_json
import util
# Maximization fitness
import time
import numpy as np
from constants import MAX_RADIUS_OF_INFLUENCE
from tqdm import tqdm

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", MyIndividual, fitness=creator.FitnessMax)


def optimize_cluster(cluster, constraints, data, settings: dict = None):
    toolbox = base.Toolbox()

    toolbox.register("individual", settings["create_individual"])
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", settings["evaluate"])
    toolbox.register("mate", settings["mate"])
    toolbox.register("mutate", settings["mutate"])
    toolbox.register("select", tools.selTournament, tournsize=settings["tournsize"])
    toolbox.register("clone", settings["clone"])
    population = toolbox.population(n=settings["population_size"])

    for ind in population:
        fit = toolbox.evaluate(ind)

    for gen in tqdm(range(settings["generations"]), disable=True):
        offspring = toolbox.select(population, len(population) - settings["elitism"])
        offspring = list(map(toolbox.clone, offspring))

        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < settings["crossover_probability"]:
                toolbox.mate(child1, child2)
                child1.fitness = None
                child2.fitness = None

        for mutant in offspring:
            if random.random() < settings["mutation_probability"]:
                toolbox.mutate(mutant)
                mutant.fitness = None

        for ind in offspring:
            fit = toolbox.evaluate(ind)
        population = sorted(population, key=lambda x: x.fitness, reverse=True)
        population = population[:settings["elitism"]] + offspring
        best_individual = tools.selBest(population, 1)[0]
        print("Best fitness:", best_individual.fitness)
        # print(f"Population fitnesses: {[ind.fitness for ind in population]}")
        # print(f"Generation {gen}:  Fitness: {best_individual.fitness}")
    return population, best_individual


def main():
    clusters = load_json("data/simple_cluster.json")
    constraints = load_json("data/constraints.json")
    data = load_json("data/sample_profit.json")

    cluster = clusters[0]
    f_fitness = FastIntersectUnionFitness(cluster, constraints, data)

    crossover = CrossoverGeometric(0.1)
    mutator = MutatorSimple(0.5, 1)
    # Example settings for the optimization process
    settings = {
        "create_individual": lambda: create_individual_heuristic1(cluster, constraints, data),
        "evaluate": lambda ind: f_fitness(ind),
        "mate": lambda ind1, ind2: crossover(ind1, ind2),
        "mutate": lambda ind: mutator(ind),
        "tournsize": 3,
        "clone": lambda ind: ind.copy(),
        "population_size": 50,
        "generations": 90,
        "crossover_probability": 0.8,
        "mutation_probability": 0.8,
        "elitism": 1,
    }

    p, best_individual = optimize_cluster(cluster, constraints, data, settings)
    random_ind = create_individual_heuristic1(cluster, constraints, data)

    store_json(individual_to_json(random_ind), "results/random_individual.json")
    store_json(individual_to_json(best_individual), "results/solution.json")


def test():
    clusters = load_json("data/simple_cluster.json")
    constraints = load_json("data/constraints.json")
    data = load_json("data/sample_profit.json")

    cluster = clusters[0]

    fitness = IntersectUnionFitness(cluster, constraints, data)
    f_fitness = FastIntersectUnionFitness(cluster, constraints, data)
    rnd_ind = create_individual_heuristic1(cluster, constraints, data)

    sums = rnd_ind.big_matrix.sum(axis=0, keepdims=True)
    sums[sums == 0] = 1
    solution_matrix = rnd_ind.big_matrix / sums
    solution_matrix = np.sqrt(solution_matrix) * MAX_RADIUS_OF_INFLUENCE

    data_per_sunday = []
    data_per_sunday1 = []
    m = -9999
    for sunday in range(rnd_ind.constraints["SUNDAYS"]):
        radii = solution_matrix[:, sunday]
        coords = [rnd_ind.data[id_]["coordinates"] for id_ in rnd_ind.cluster]
        boxes = util.fast_create_boxes(coords, radii)
        other_boxes = [util.create_box(rnd_ind.data[id_]["coordinates"][1], rnd_ind.data[id_]
                                       ["coordinates"][0], radius) for id_, radius in zip(rnd_ind.cluster, radii)]
        other_boxes_ = np.array([box.bounds for box in other_boxes])
        union, intersect = util.fast_union_intersect(boxes)
        union1, intersect1 = util.union_intersect(other_boxes)
        m = max(m, abs(union - intersect - union1 + intersect1))

        data_per_sunday.append(union - intersect)
        data_per_sunday1.append(union1 - intersect1)
    print(f"Max diff: {m}")
    print(f"Average diff: {np.average(np.abs(data_per_sunday) - np.average(data_per_sunday1))}")
    start = time.time()
    f1 = fitness(rnd_ind)
    end = time.time()
    print(f"Time taken for fitness calculation: {end - start} seconds")
    start = time.time()
    f2 = f_fitness(rnd_ind)
    end = time.time()
    print(f"Time taken for fast fitness calculation: {end - start} seconds")
    print(f"Difference in fitness: {f1[0] - f2[0]}")


if __name__ == "__main__":
    main()
