package project.genetic.generator;

import project.genetic.chromosome.Chromosome;

import java.util.ArrayList;
import java.util.List;

/**
 * Generator is used to generate new chromosomes.
 */
public interface Generator<T extends Chromosome> {

    public T generate();

    default List<T> generateMany(int n) {
        List<T> results = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            results.add(this.generate());
        }

        return results;
    }
}
