package project.settings;

import project.genetic.chromosome.MatrixChromosome;
import project.genetic.crossover.CompositeCrossover;
import project.genetic.crossover.GeometricColumnCrossover;
import project.genetic.crossover.GeometricRowCrossover;
import project.genetic.crossover.SinglePointCrossover;
import project.genetic.eliminator.EliteGeometricEliminator;
import project.genetic.fitness.FastIntersectUnionFitness;
import project.genetic.generator.AllSundaysHaveWorkGenerator;
import project.genetic.logger.SoutLogger;
import project.genetic.mutator.CompositeMutator;
import project.genetic.mutator.RandomSimpleMutator;
import project.genetic.selection.TournamentSelection;

import java.util.ArrayList;
import java.util.List;

public class SmallRunSettings extends Settings<MatrixChromosome> {

    {
        this.name = "SmallRunSettings";

        this.populationSize = 10000;
        this.generations = 8000;
        this.newChromosomes = 24;
        this.deterministic = true;

        this.mutator = new CompositeMutator<>(1, List.of(new RandomSimpleMutator(5, 0.5)), new double[]{1});
        this.crossover = new CompositeCrossover<>(1, List.of(
                new GeometricColumnCrossover(0.3, 0.7),
                new GeometricRowCrossover(0.3, 0.7),
                new SinglePointCrossover(0.5)
        ),
                new double[]{0.4, 0.4, 0.2});
        this.selection = new TournamentSelection(3);
        this.fitness = new FastIntersectUnionFitness();
        this.generator = new AllSundaysHaveWorkGenerator(new ArrayList<>());
        this.eliminator = new EliteGeometricEliminator(0.2, 0.89);
        this.logger = new SoutLogger();

    }
}
