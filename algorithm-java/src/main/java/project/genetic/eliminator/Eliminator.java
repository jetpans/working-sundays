package project.genetic.eliminator;

import project.genetic.chromosome.Chromosome;

import java.util.List;

public interface Eliminator {
    public <T extends Chromosome> List<T> select(List<T> population);
}