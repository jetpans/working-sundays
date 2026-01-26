package project.genetic.crossover;

import project.genetic.chromosome.MatrixChromosome;
import project.models.Global;
import project.models.Problem;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class ColumnKSwitchCrossover implements Crossover<MatrixChromosome> {
    private int k;
    private double p;

    public ColumnKSwitchCrossover(int k, double p) {
        this.k = k;
        this.p = p;
    }

    @Override
    public List<MatrixChromosome> crossover(MatrixChromosome parent1, MatrixChromosome parent2) {
        if (Global.RANDOM.nextDouble() > p) {
            return List.of(new MatrixChromosome(parent1), new MatrixChromosome(parent2));
        }

        MatrixChromosome child1 = new MatrixChromosome(parent1);
        MatrixChromosome child2 = new MatrixChromosome(parent2);

        int totalSundays = Problem.getInstance().totalSundays;
        int numStores = child1.getModel().size();
        int actualK = Math.min(k, totalSundays);

        // 1. Select K random unique Sundays
        List<Integer> sundays = new ArrayList<>(totalSundays);
        for (int i = 0; i < totalSundays; i++) sundays.add(i);
        Collections.shuffle(sundays, Global.RANDOM);
        List<Integer> selectedSundays = sundays.subList(0, actualK);

        for (Integer sunday : selectedSundays) {
            for (int storeIdx = 0; storeIdx < numStores; storeIdx++) {
                // TODO: Check this faster using the matrix representation?
                boolean c1Works = child1.getModel(storeIdx).contains(sunday);
                boolean c2Works = child2.getModel(storeIdx).contains(sunday);

                // If both work or neither work, swapping changes nothing regarding this Sunday
                if (c1Works == c2Works) continue;

                if (c1Works) {
                    // Case: Child1 works, Child2 does not.
                    // Action: Child1 stops working, Child2 starts working.

                    // 1. Move Sunday from Child1 Model to AntiModel
                    child1.removeFromModel(storeIdx, sunday);

                    // 2. Move Sunday from Child2 AntiModel to Model
                    child2.moveToModel(storeIdx, sunday);

                    // 3. Fix counts
                    // Child1 is now -1 below capacity. Add random from AntiModel.
                    if (!child1.getAntiModel(storeIdx).isEmpty()) {
                        int randIdx = Global.RANDOM.nextInt(child1.getAntiModel(storeIdx).size());
                        child1.fromAntiModelToModel(storeIdx, randIdx);
                    }

                    // Child2 is now +1 above capacity. Remove random from Model.
                    if (!child2.getModel(storeIdx).isEmpty()) {
                        int randIdx = Global.RANDOM.nextInt(child2.getModel(storeIdx).size());
                        child2.fromModelToAntiModel(storeIdx, randIdx);
                    }

                } else {
                    // Case: Child2 works, Child1 does not. (Symmetric to above)

                    child2.removeFromModel(storeIdx, sunday);
                    child1.moveToModel(storeIdx, sunday);

                    // Fix counts
                    // Child2 needs +1
                    if (!child2.getAntiModel(storeIdx).isEmpty()) {
                        int randIdx = Global.RANDOM.nextInt(child2.getAntiModel(storeIdx).size());
                        child2.fromAntiModelToModel(storeIdx, randIdx);
                    }

                    // Child1 needs -1
                    if (!child1.getModel(storeIdx).isEmpty()) {
                        int randIdx = Global.RANDOM.nextInt(child1.getModel(storeIdx).size());
                        child1.fromModelToAntiModel(storeIdx, randIdx);
                    }
                }
            }
        }

        return List.of(child1, child2);
    }
}