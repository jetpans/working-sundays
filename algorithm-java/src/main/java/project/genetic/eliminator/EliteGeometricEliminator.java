package project.genetic.eliminator;

import project.Util;
import project.genetic.chromosome.Chromosome;
import project.models.Global;

import java.util.ArrayList;
import java.util.List;

public class EliteGeometricEliminator implements Eliminator {
    private final double survivalRate;
    private final double p;

    public EliteGeometricEliminator(double survivalRate, double p) {
        this.survivalRate = survivalRate;
        this.p = p;
    }

    @Override
    public <T extends Chromosome> List<T> select(List<T> population) {
        int numToSurvive = (int) Math.ceil(population.size() * survivalRate);

        List<T> nextPopulation = new ArrayList<>(List.of(population.getLast()));
        while (nextPopulation.size() < numToSurvive) {
            int index = population.size() - Util.randomGeometric(population.size(), this.p, Global.RANDOM);
            for (int i = index; i < population.size() - 1; i++) {
                if (!nextPopulation.contains(population.get(i))) {
                    nextPopulation.add(population.get(i));
                    break;
                }
            }

        }
        return nextPopulation;
    }
}
