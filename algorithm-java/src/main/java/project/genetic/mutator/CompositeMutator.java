package project.genetic.mutator;

import project.genetic.chromosome.Chromosome;
import project.models.Global;

import java.util.List;

public class CompositeMutator<T extends Chromosome> implements Mutator<T> {
    private final List<Mutator<T>> mutators;
    private final double[] weights;
    private final double p;

    public CompositeMutator(double p, List<Mutator<T>> mutators, double[] weights) {
        this.p = p;
        this.mutators = mutators;
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
    public void mutate(T c) {
        if (Global.RANDOM.nextDouble() > p) {
            return;
        }
        double rand = Global.RANDOM.nextDouble();
        double cumulativeWeight = 0.0;
        Mutator<T> mutator = mutators.get(mutators.size() - 1);
        for (int i = 0; i < mutators.size(); i++) {
            cumulativeWeight += weights[i];
            if (rand <= cumulativeWeight) {
                mutator = mutators.get(i);
                break;
            }
        }
        mutator.mutate(c);
    }
}
