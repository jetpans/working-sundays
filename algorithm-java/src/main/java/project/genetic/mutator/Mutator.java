package project.genetic.mutator;

import project.genetic.chromosome.Chromosome;

public interface Mutator<T extends Chromosome> {
    void mutate(T c);
}
