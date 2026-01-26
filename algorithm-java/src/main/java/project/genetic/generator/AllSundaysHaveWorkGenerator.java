package project.genetic.generator;

import project.genetic.chromosome.MatrixChromosome;
import project.models.Global;
import project.models.Problem;

import java.util.*;

public class AllSundaysHaveWorkGenerator extends ForStoresGenerator {

    public AllSundaysHaveWorkGenerator(List<String> storeIds) {
        super(storeIds);
    }

    @Override
    public ForStoresGenerator copyOf() {
        return new AllSundaysHaveWorkGenerator(new ArrayList<>(this.storeIds));
    }

    @Override
    public MatrixChromosome generate() {
        MatrixChromosome chromosome = new MatrixChromosome(storeIds);
        Problem problem = Problem.getInstance();

        // 1. Track which Sundays are covered by mandatory "Works" constraints
        Set<Integer> sundaysThatHaveWork = new HashSet<>();
        for (int i = 0; i < storeIds.size(); i++) {
            // MatrixChromosome constructor already populates 'works' list
            // and moves fixed works into the matrix.
            sundaysThatHaveWork.addAll(chromosome.getWorks(i));
        }

        // 2. Prioritize covering Sundays that don't have mandatory work
        List<Integer> storeIndices = new ArrayList<>();
        for (int i = 0; i < storeIds.size(); i++) storeIndices.add(i);

        for (int sunday = 0; sunday < problem.totalSundays; sunday++) {
            if (sundaysThatHaveWork.contains(sunday)) {
                continue;
            }

            // Shuffle stores to randomize which store picks up this "orphaned" Sunday
            Collections.shuffle(storeIndices, Global.RANDOM);

            for (int storeIdx : storeIndices) {
                // Conditions:
                // 1. Store must hold this Sunday in AntiModel (meaning it's free and not restricted)
                // 2. Store must have capacity
                List<Integer> antiModel = chromosome.getAntiModel(storeIdx);
                List<Integer> model = chromosome.getModel(storeIdx);
                List<Integer> works = chromosome.getWorks(storeIdx);

                if (antiModel.contains(sunday) &&
                        (model.size() + works.size() < problem.workingSundays)) {

                    // Move from AntiModel to Model using the specific value method
                    chromosome.moveToModel(storeIdx, sunday);

                    // We successfully covered this Sunday, move to next Sunday
                    break;
                }
            }
        }

        // 3. Fill the rest of the capacity randomly (same as RandomGenerator)
        for (int i = 0; i < storeIds.size(); i++) {
            while (chromosome.getModel(i).size() + chromosome.getWorks(i).size() < problem.workingSundays) {
                if (chromosome.getAntiModel(i).isEmpty()) break; // Safety check

                int randomIndex = Global.RANDOM.nextInt(chromosome.getAntiModel(i).size());
                chromosome.fromAntiModelToModel(i, randomIndex);
            }
        }

        return chromosome;
    }
}