package project.genetic.fitness;

import project.genetic.chromosome.Chromosome;


/**
 * Interface to calculate fitness of chromosome. The project follows the procedure that bigger fitness is better.
 */
public interface Fitness<T extends Chromosome> {
    double evaluate(T c);
}
