package project.genetic.crossover;

import project.genetic.chromosome.MatrixChromosome;
import project.models.Global;

import java.util.ArrayList;
import java.util.List;

public class KSwitchCrossover implements Crossover<MatrixChromosome> {
    private int k;
    private double p;

    public KSwitchCrossover(int k, double p) {
        this.k = k;
        this.p = p;
    }

    @Override
    public List<MatrixChromosome> crossover(MatrixChromosome parent1, MatrixChromosome parent2) {
        if (Global.RANDOM.nextDouble() > p) {
            return List.of(parent1, parent2);
        }
        MatrixChromosome child1 = new MatrixChromosome(parent1);
        MatrixChromosome child2 = new MatrixChromosome(parent2);
        for (int blah = 0; blah < k; blah++) {
            int storeIndex = Global.RANDOM.nextInt(child1.getModel().size());
            List<Integer> tempModel1 = new ArrayList<>(child1.getModel(storeIndex));
            child1.setModel(storeIndex, child2.getModel(storeIndex));
            child2.setModel(storeIndex, tempModel1);
        }

        return List.of(child1, child2);
    }
}
