package project.genetic.selection;

import project.genetic.chromosome.Chromosome;

import java.util.List;

/**
 * Usually returns 2 chromosomes FROM candidates based on some logic, but can return any number. Candidates has to be sorted.
 */

public interface Selection {
    public <T extends Chromosome> List<T> select(List<T> candidates);
}
