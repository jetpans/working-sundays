import random
from deap import base, creator, tools
import numpy as np
from shapely.geometry import box
from util import create_box, union_intersect, fast_create_boxes, fast_union_intersect, haversine
from constants import MAX_RADIUS_OF_INFLUENCE


class MyIndividual:
    def __init__(self, cluster, constraints, data):
        self.cluster = cluster
        self.constraints = constraints
        self.data = data
        self.fitness = None

        self.works = [[] for _ in range(len(cluster))]
        self.model = [[] for _ in range(len(cluster))]
        self.antimodel = [[] for _ in range(len(cluster))]
        self.big_matrix = np.zeros((len(cluster), constraints["SUNDAYS"]))

    def copy(self):
        new_ind = MyIndividual(self.cluster, self.constraints, self.data)

        new_ind.works = [work[::] for work in self.works]
        new_ind.model = [model[::] for model in self.model]
        new_ind.antimodel = [antimodel[::] for antimodel in self.antimodel]
        new_ind.big_matrix = self.big_matrix.copy()
        if hasattr(self, "fitness"):
            new_ind.fitness = self.fitness.copy()
        return new_ind

    def __repr__(self):
        return f"{self.works + self.model}"


def create_individual_random(cluster, constraints, data):
    # just like random init
    ind = MyIndividual(cluster, constraints, data)
    for index, id_ in enumerate(cluster):
        ind.works[index] = constraints[id_]["works"]
        for i in range(constraints["SUNDAYS"]):
            if i not in ind.works[index] and i not in constraints[id_]["doesnt_work"]:
                ind.antimodel[index].append(i)

        while len(ind.model[index]) + len(ind.works[index]) < constraints["MAX_WORKS"]:
            rnd = random.randint(0, len(ind.antimodel[index]) - 1)
            elem = ind.antimodel[index][rnd]
            ind.model[index].append(elem)
            ind.antimodel[index].pop(rnd)

            ind.big_matrix[index][elem] = ind.data[id_]["user_ratings_total"]  # Put model entries in the big matrix

        for w in ind.works[index]:
            ind.big_matrix[index][w] = ind.data[id_]["user_ratings_total"]  # Put works entries in the big matrix
    return ind


def create_individual_heuristic1(cluster, constraints, data):
    ind = MyIndividual(cluster, constraints, data)
    sundays_that_have_work = set()
    for index, id_ in enumerate(cluster):
        ind.works[index] = constraints[id_]["works"]
        sundays_that_have_work.update(ind.works[index])
        for i in range(constraints["SUNDAYS"]):
            if i not in ind.works[index] and i not in constraints[id_]["doesnt_work"]:
                ind.antimodel[index].append(i)
    for sunday in range(constraints["SUNDAYS"]):
        if sunday in sundays_that_have_work:
            continue
        for index, id_ in enumerate(np.random.permutation(cluster)):
            if sunday in ind.antimodel[index] and len(ind.model[index]) + len(ind.works[index]) < constraints["MAX_WORKS"]:
                ind.model[index].append(sunday)
                ind.antimodel[index].remove(sunday)
                ind.big_matrix[index][sunday] = data[id_]["user_ratings_total"]
                break

    for index, id_ in enumerate(cluster):
        while len(ind.model[index]) + len(ind.works[index]) < constraints["MAX_WORKS"]:
            rnd = random.randint(0, len(ind.antimodel[index]) - 1)
            elem = ind.antimodel[index][rnd]
            ind.model[index].append(elem)
            ind.antimodel[index].pop(rnd)

            ind.big_matrix[index][elem] = ind.data[id_]["user_ratings_total"]  # Put model entries in the big matrix

        for w in ind.works[index]:
            ind.big_matrix[index][w] = ind.data[id_]["user_ratings_total"]  # Put works entries in the big matrix
    return ind


def create_individual_based_on_others_heuristic1(cluster, constraints, data, inds: list = None):
    if inds is None or len(inds) == 0:
        ind = MyIndividual(cluster, constraints, data)
        sundays_that_have_work = set()
        for index, id_ in enumerate(cluster):
            ind.works[index] = constraints[id_]["works"]
            sundays_that_have_work.update(ind.works[index])
            for i in range(constraints["SUNDAYS"]):
                if i not in ind.works[index] and i not in constraints[id_]["doesnt_work"]:
                    ind.antimodel[index].append(i)
        for sunday in range(constraints["SUNDAYS"]):
            if sunday in sundays_that_have_work:
                continue
            for index, id_ in enumerate(np.random.permutation(cluster)):
                if sunday in ind.antimodel[index] and len(ind.model[index]) + len(ind.works[index]) < constraints["MAX_WORKS"]:
                    ind.model[index].append(sunday)
                    ind.antimodel[index].remove(sunday)
                    ind.big_matrix[index][sunday] = data[id_]["user_ratings_total"]
                    break

        for index, id_ in enumerate(cluster):
            while len(ind.model[index]) + len(ind.works[index]) < constraints["MAX_WORKS"]:
                rnd = random.randint(0, len(ind.antimodel[index]) - 1)
                elem = ind.antimodel[index][rnd]
                ind.model[index].append(elem)
                ind.antimodel[index].pop(rnd)

                ind.big_matrix[index][elem] = ind.data[id_]["user_ratings_total"]  # Put model entries in the big matrix

            for w in ind.works[index]:
                ind.big_matrix[index][w] = ind.data[id_]["user_ratings_total"]  # Put works entries in the big matrix
        return ind
    else:
        new_ind = MyIndividual(cluster, constraints, data)
        for other_ind in inds:
            for index, store_id in enumerate(cluster):
                if store_id not in other_ind.cluster:
                    continue
                my_index = new_ind.cluster.index(store_id)
                other_index = other_ind.cluster.index(store_id)
                new_ind.works[my_index] = other_ind.works[other_index][::]
                new_ind.model[my_index] = other_ind.model[other_index][::]
                new_ind.antimodel[my_index] = other_ind.antimodel[other_index][::]
                new_ind.big_matrix[my_index] = other_ind.big_matrix[other_index].copy()

        for index, value in enumerate(new_ind.model):
            lnt = len(value) + len(new_ind.works[index])
            assert lnt == constraints["MAX_WORKS"], f"Model is incorrect {cluster[index]}, instead lnt is {lnt}"
        return new_ind


def mutate_individual_simple(individual, prob, count):
    for index in range(len(individual.model)):
        if len(individual.model[index]) == 0:
            continue
        if random.random() < prob:
            for _ in range(count):
                if len(individual.model[index]) == 0 or len(individual.antimodel[index]) == 0:
                    break
                rnd1 = random.randint(0, len(individual.model[index]) - 1)
                rnd2 = random.randint(0, len(individual.antimodel[index]) - 1)
                elem = individual.model[index][rnd1]
                individual.model[index][rnd1] = individual.antimodel[index][rnd2]
                individual.antimodel[index][rnd2] = elem
                individual.big_matrix[index][elem] = 0  # Remove from big matrix
                other_elem = individual.antimodel[index][rnd2]

                individual.big_matrix[index][other_elem] = individual.data[individual.cluster[index]
                                                                           # Put new entry in big matrix
                                                                           ]["user_ratings_total"]


def crossover_individuals_kswitch(ind1, ind2, k):
    c1, c2 = ind1, ind2
    k = min(len(ind1.model), k)

    indices = np.random.choice(range(len(ind1.model)), k, replace=False)
    for index in indices:
        if len(c1.model[index]) == 0 or len(c2.model[index]) == 0:
            continue
        c1.model[index], c2.model[index] = c2.model[index][::], c1.model[index][::]

        # Swap rows in big matrix
        c1.big_matrix[index], c2.big_matrix[index] = c2.big_matrix[index], c1.big_matrix[index]

        c1.antimodel[index], c2.antimodel[index] = c2.antimodel[index][::], c1.antimodel[index][::]


def crossover_individuals_singlepoint(ind1, ind2):
    c1, c2 = ind1, ind2
    index = random.randint(0, len(ind1.model) - 1)
    for i in range(index, len(ind1.model)):
        if len(c1.model[i]) == 0 or len(c2.model[i]) == 0:
            continue
        c1.model[i], c2.model[i] = c2.model[i][::], c1.model[i][::]
        c1.antimodel[i], c2.antimodel[i] = c2.antimodel[i][::], c1.antimodel[i][::]
        c1.big_matrix[i], c2.big_matrix[i] = c2.big_matrix[i], c1.big_matrix[i]  # Swap rows in big matrix


def crossover_individuals_columns_kswitch(ind1, ind2, k):
    c1, c2 = ind1, ind2
    k = min(ind1.constraints["SUNDAYS"], k)

    indices = np.random.choice(range(ind1.constraints["SUNDAYS"]), k, replace=False)
    for index in indices:
        sunday = index
        for shop in range(len(c1.model)):
            if sunday in c1.model[shop] and sunday in c2.model[shop]:
                continue
            if sunday not in c1.model[shop] and sunday not in c2.model[shop]:
                continue
            if sunday in c2.model[shop]:
                c1, c2 = c2, c1
            # Sunday in c1 and not in c2
            # sunday in c1 and not in c2
            # remove it from c1 and add to c2 models
            # add it to c1 antimodel, remove from c2 antimodel
            # Adjust big matrix
            c1.model[shop].remove(sunday)
            c2.model[shop].append(sunday)
            c1.antimodel[shop].append(sunday)
            c2.antimodel[shop].remove(sunday)
            c1.big_matrix[shop][sunday] = 0  # Remove from big matrix
            c2.big_matrix[shop][sunday] = c1.data[c1.cluster[shop]]["user_ratings_total"]  # Put new entry in big matrix

            # Fix them, c2 has one too many, c1 has one too few
            removec2 = c2.model[shop].pop(random.randint(0, len(c2.model[shop]) - 1))
            addtoc1 = c1.antimodel[shop].pop(random.randint(0, len(c1.antimodel[shop]) - 1))
            c1.model[shop].append(addtoc1)
            c2.antimodel[shop].append(removec2)
            c1.big_matrix[shop][addtoc1] = c1.data[c1.cluster[shop]
                                                   ]["user_ratings_total"]  # Put new entry in big matrix
            c2.big_matrix[shop][removec2] = 0  # Remove from big matrix

    for index in range(len(c1.model)):
        assert len(c1.model[index]) + len(c1.works[index]
                                          ) == c1.constraints["MAX_WORKS"], f"Model is incorrect {c1.cluster[index]}"
        assert len(c2.model[index]) + len(c2.works[index]
                                          ) == c2.constraints["MAX_WORKS"], f"Model is incorrect {c2.cluster[index]}"


class Fitness:
    def __init__(self, *args):
        self.args = args

    def __call__(self, individual):
        raise NotImplementedError("Fitness function not implemented")


class IntersectUnionFitness(Fitness):
    """MAX Fitness function that calculates the average area of the union of boxes minus the intersection."""

    def __init__(self, *args):
        super().__init__(*args)

    def __call__(self, individual):
        # Normalize each column of the big matirx
        sums = individual.big_matrix.sum(axis=0, keepdims=True)
        sums[sums == 0] = 1
        solution_matrix = individual.big_matrix / sums
        solution_matrix = np.sqrt(solution_matrix) * MAX_RADIUS_OF_INFLUENCE

        data_per_sunday = []

        for sunday in range(individual.constraints["SUNDAYS"]):
            current_sunday = []
            for index, id_ in enumerate(individual.cluster):
                lon, lat = individual.data[id_]["coordinates"]
                current_sunday.append(create_box(lon, lat, solution_matrix[index][sunday]))

            union, intersect = union_intersect(current_sunday)
            data_per_sunday.append(union - intersect)
        individual.fitness = np.average(data_per_sunday)
        return (individual.fitness,)


class FastIntersectUnionFitness(Fitness):
    def __init__(self, *args):
        super().__init__(*args)

    def __call__(self, individual):
        sums = individual.big_matrix.sum(axis=0, keepdims=True)
        sums[sums == 0] = 1
        solution_matrix = individual.big_matrix / sums
        solution_matrix = np.sqrt(solution_matrix) * MAX_RADIUS_OF_INFLUENCE

        data_per_sunday = []

        for sunday in range(individual.constraints["SUNDAYS"]):
            radii = solution_matrix[:, sunday]
            coords = [individual.data[id_]["coordinates"] for id_ in individual.cluster]
            boxes = fast_create_boxes(coords, radii)
            union, intersect = fast_union_intersect(boxes)
            data_per_sunday.append(union - intersect)

        individual.fitness = np.average(data_per_sunday)
        return (individual.fitness,)


class Crossover:
    def __init__(self, *args):
        self.args = args

    def __call__(self, ind1, ind2):
        raise NotImplementedError("Crossover method not implemented")


class CrossoverKSwitch(Crossover):
    def __init__(self, k):
        super().__init__(k)
        self.k = k

    def __call__(self, ind1, ind2):
        crossover_individuals_kswitch(ind1, ind2, self.k)


class CrossoverGeometric(Crossover):
    def __init__(self, p: float):
        super().__init__(p)
        self.p = p

    def __call__(self, ind1, ind2):
        k = min(np.random.geometric(self.p), len(ind1.model) - 1)
        crossover_individuals_kswitch(ind1, ind2, k)


class CrossoverSinglePoint(Crossover):
    def __call__(self, ind1, ind2):
        crossover_individuals_singlepoint(ind1, ind2)


class CrossoverColumnGeometric(Crossover):
    def __init__(self, p: float):
        super().__init__(p)
        self.p = p

    def __call__(self, ind1, ind2):
        k = min(np.random.geometric(self.p), len(ind1.model) - 1)
        crossover_individuals_columns_kswitch(ind1, ind2, k)


class Mutator:
    def __init__(self, *args):
        self.args = args

    def __call__(self, individual):
        raise NotImplementedError("Mutation method not implemented")


class MutatorSimple(Mutator):
    def __init__(self, prob, count):
        super().__init__(prob, count)
        self.prob = prob
        self.count = count

    def __call__(self, individual):
        mutate_individual_simple(individual, self.prob, self.count)
