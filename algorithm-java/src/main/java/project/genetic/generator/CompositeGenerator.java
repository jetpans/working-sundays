package project.genetic.generator;

import project.genetic.chromosome.Chromosome;
import project.models.Global;

import java.util.List;

public class CompositeGenerator<T extends Chromosome> implements Generator<T> {
    private final List<Generator<T>> generators;
    private final double[] weights;

    public CompositeGenerator(List<Generator<T>> generators, double[] weights) {
        this.generators = generators;
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
    public T generate() {
        double rand = Global.RANDOM.nextDouble();
        double cumulativeWeight = 0.0;
        Generator<T> generator = generators.get(generators.size() - 1);
        for (int i = 0; i < generators.size(); i++) {
            cumulativeWeight += weights[i];
            if (rand <= cumulativeWeight) {
                generator = generators.get(i);
                break;
            }
        }
        return generator.generate();
    }
}
