package project.genetic.crossover;

import project.genetic.chromosome.MatrixChromosome;
import project.models.Global;

import java.util.List;

public class GeometricColumnCrossover implements Crossover<MatrixChromosome> {
    private double geoP; // Geometric distribution probability parameter
    private double crossoverProb;

    public GeometricColumnCrossover(double geoP, double crossoverProb) {
        this.geoP = geoP;
        this.crossoverProb = crossoverProb;
    }

    @Override
    public List<MatrixChromosome> crossover(MatrixChromosome parent1, MatrixChromosome parent2) {
        // Calculate K based on geometric distribution
        // Python: np.random.geometric(p)
        // Java Manual: floor(ln(U) / ln(1-p)) + 1
        int k = (int) (Math.log(Global.RANDOM.nextDouble()) / Math.log(1.0 - geoP)) + 1;

        // Use the ColumnKSwitch logic with the dynamically generated K
        // We reuse the logic by delegating.
        ColumnKSwitchCrossover delegate = new ColumnKSwitchCrossover(k, crossoverProb);
        return delegate.crossover(parent1, parent2);
    }
}