package project.genetic.eliminator;

import project.genetic.chromosome.Chromosome;

import java.util.ArrayList;
import java.util.List;

public class EliteEliminator implements Eliminator {
    private int elitism;

    public EliteEliminator(int elitism) {
        this.elitism = elitism;
    }

    @Override
    public <T extends Chromosome> List<T> select(List<T> population) {
        if (Math.random() < 0.001) {
            // Check if population sorted
            for (int i = 1; i < population.size(); i++) {
                if (population.get(i).fitness < population.get(i - 1).fitness) {
                    throw new RuntimeException("Population not sorted in EliteEliminator");
                }
            }
        }
        return new ArrayList<>(population.subList(population.size() - this.elitism, population.size()));
    }
}
