package project.genetic.mutator;

import project.genetic.chromosome.MatrixChromosome;
import project.models.Global;

public class RandomSimpleMutator implements Mutator<MatrixChromosome> {
    private int numMutations;
    private double p;

    public RandomSimpleMutator(int numMutations, double p) {
        this.numMutations = numMutations;
        this.p = p;
    }

    @Override
    public void mutate(MatrixChromosome c) {
        if (Global.RANDOM.nextDouble() > p) return;

        for (int blah = 0; blah < numMutations; blah++) {
            if (c.getModel().isEmpty()) continue;
            int storeIndex = Global.RANDOM.nextInt(c.getModel().size());
            if (c.getModel(storeIndex).isEmpty() || c.getAntiModel(storeIndex).isEmpty()) continue;
            int r = Global.RANDOM.nextInt(c.getModel(storeIndex).size());
            c.fromModelToAntiModel(storeIndex, r);
            r = Global.RANDOM.nextInt(c.getAntiModel(storeIndex).size());
            c.fromAntiModelToModel(storeIndex, r);
        }
    }
}
