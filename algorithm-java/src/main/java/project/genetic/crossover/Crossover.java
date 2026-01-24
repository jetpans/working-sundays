package project.genetic.crossover;

import project.genetic.chromosome.Chromosome;

import java.util.List;

/**
 * Interface to create 2 children from two parents.
 */

public interface Crossover<T extends Chromosome> {
    List<T> crossover(T parent1, T parent2);
}
