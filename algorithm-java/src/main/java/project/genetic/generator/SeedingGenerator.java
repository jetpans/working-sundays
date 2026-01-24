package project.genetic.generator;

import project.genetic.chromosome.MatrixChromosome;
import project.models.Problem;

import java.util.ArrayList;
import java.util.List;

public class SeedingGenerator implements Generator<MatrixChromosome> {

    private final List<String> storeIds;
    private final List<MatrixChromosome> seeds;
    private final Generator<MatrixChromosome> fallbackGenerator;

    /**
     * @param storeIds The list of store IDs for the new chromosome.
     * @param seeds    Optional list of individuals to copy from. Can be null or empty.
     */
    public SeedingGenerator(List<String> storeIds, List<MatrixChromosome> seeds, Generator<MatrixChromosome> fallbackGenerator) {
        this.storeIds = storeIds;
        this.seeds = seeds;
        this.fallbackGenerator = fallbackGenerator;
    }

    @Override
    public MatrixChromosome generate() {
        // CASE 1: No seeds provided.
        // Fallback to Heuristic 1 (Cover empty Sundays, then fill random).
        if (seeds == null || seeds.isEmpty()) {
            return fallbackGenerator.generate();
        }

        // CASE 2: Seeds provided.
        // Create new individual and layer seeds on top.
        MatrixChromosome child = new MatrixChromosome(storeIds);

        for (MatrixChromosome seed : seeds) {
            List<String> seedStoreIds = seed.storeIds;

            // Optimization: If store IDs are exactly the same order (common in GAs)
            boolean exactOrder = seedStoreIds.equals(storeIds);

            for (int i = 0; i < storeIds.size(); i++) {
                String myStoreId = storeIds.get(i);

                int seedStoreIndex;
                if (exactOrder) {
                    seedStoreIndex = i;
                } else {
                    seedStoreIndex = seedStoreIds.indexOf(myStoreId);
                }

                // If the seed contains this store, copy its schedule
                if (seedStoreIndex != -1) {
                    // We extract the model (list of working Sundays) from the seed
                    // We MUST create a new ArrayList to avoid reference sharing between chromosomes
                    List<Integer> seedModel = new ArrayList<>(seed.getModel(seedStoreIndex));

                    // setModel automatically:
                    // 1. Clears the current model/antimodel for store 'i'
                    // 2. Assigns the new days
                    // 3. Recalculates the Matrix bits (0 or Metric)
                    // 4. Recalculates the AntiModel based on constraints
                    child.setModel(i, seedModel);
                }
            }
        }

        // Validation (matches Python assertion):
        // Ensure the generated individual respects the capacity constraints
        Problem problem = Problem.getInstance();
        for (int i = 0; i < storeIds.size(); i++) {
            int total = child.getModel(i).size() + child.getWorks(i).size();
            if (total != problem.workingSundays) {
                throw new IllegalStateException("Seeded generation produced invalid model length for store " + storeIds.get(i));
            }
        }

        return child;
    }


}
