package project.genetic.generator;

import project.genetic.chromosome.MatrixChromosome;
import project.models.Global;
import project.models.Problem;

import java.util.ArrayList;
import java.util.List;

public class RandomGenerator extends ForStoresGenerator {


    public RandomGenerator(List<String> storeIds) {
        super(storeIds);
    }

    @Override
    public ForStoresGenerator copyOf() {
        return new RandomGenerator(new ArrayList<>(this.storeIds));
    }

    @Override
    public MatrixChromosome generate() {
        MatrixChromosome chromosome = new MatrixChromosome(storeIds);
        for (int i = 0; i < storeIds.size(); i++) {
            while (chromosome.getModel(i).size() + chromosome.getWorks(i).size() < Problem.getInstance().workingSundays) {
                int randomIndex = Global.RANDOM.nextInt(chromosome.getAntiModel(i).size());
                chromosome.fromAntiModelToModel(i, randomIndex);
            }
        }
        return chromosome;
    }
}
