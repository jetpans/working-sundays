package project.genetic.crossover;

import project.genetic.chromosome.Chromosome;
import project.models.Global;

import java.util.List;

public class CompositeCrossover<T extends Chromosome> implements Crossover<T> {
    private final List<Crossover<T>> crossovers;
    private final double[] weights;
    private final double p;

    public CompositeCrossover(double p, List<Crossover<T>> crossovers, double[] weights) {
        this.p = p;
        this.crossovers = crossovers;
        this.weights = weights;
        double totalWeight = 0.0;
        for (double weight : weights) {
            totalWeight += weight;
        }
        for (int i = 0; i < weights.length; i++) {
            weights[i] /= totalWeight;
        }
    }

    @Override
    public List<T> crossover(T parent1, T parent2) {
        if (Global.RANDOM.nextDouble() > p) {
            return List.of(parent1, parent2);
        }
        double rand = Global.RANDOM.nextDouble();
        double cumulativeWeight = 0.0;
        Crossover<T> crossover = crossovers.get(crossovers.size() - 1);
        for (int i = 0; i < crossovers.size(); i++) {
            cumulativeWeight += weights[i];
            if (rand <= cumulativeWeight) {
                crossover = crossovers.get(i);
                break;
            }
        }
        return crossover.crossover(parent1, parent2);
    }
}
