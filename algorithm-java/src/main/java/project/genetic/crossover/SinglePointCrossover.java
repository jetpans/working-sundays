package project.genetic.crossover;

import project.genetic.chromosome.MatrixChromosome;
import project.models.Global;

import java.util.ArrayList;
import java.util.List;

public class SinglePointCrossover implements Crossover<MatrixChromosome> {
    private double p;

    public SinglePointCrossover(double p) {
        this.p = p;
    }

    @Override
    public List<MatrixChromosome> crossover(MatrixChromosome parent1, MatrixChromosome parent2) {
        if (Global.RANDOM.nextDouble() > p) {
            return List.of(new MatrixChromosome(parent1), new MatrixChromosome(parent1));
        }

        MatrixChromosome child1 = new MatrixChromosome(parent1);
        MatrixChromosome child2 = new MatrixChromosome(parent2);

        int numStores = child1.getModel().size();
        int crossoverPoint = Global.RANDOM.nextInt(numStores);

        for (int i = crossoverPoint; i < numStores; i++) {
            List<Integer> model1 = new ArrayList<>(child1.getModel(i));
            List<Integer> model2 = new ArrayList<>(child2.getModel(i));
            child1.setModel(i, model2);
            child2.setModel(i, model1);
        }

        return List.of(child1, child2);
    }
}