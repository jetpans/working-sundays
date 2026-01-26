package project.executables;

import project.Util;
import project.genetic.chromosome.MatrixChromosome;
import project.genetic.fitness.CorrectFitness;
import project.genetic.fitness.FastIntersectUnionFitness;
import project.genetic.fitness.Fitness;
import project.genetic.generator.Generator;
import project.genetic.generator.RandomGenerator;
import project.models.Global;
import project.models.Problem;

import java.util.ArrayList;
import java.util.List;

public class TestFitnessFunction {


    public static void main(String[] args) {
        int NO_CHROMOSOMES = 100;

        String instanceFolder = args[0];
        String dataPath = instanceFolder + "/data.json";
        String constraintPath = instanceFolder + "/constraints.json";

        Problem.load(constraintPath, dataPath);
        List<List<String>> clusters = Util.generateClusters(Problem.getInstance().storeIds, 10, 3, Global.RANDOM);
        List<String> storeIds = clusters.get(0);

        Generator<MatrixChromosome> generator = new RandomGenerator(storeIds);

        List<MatrixChromosome> chromosomes = generator.generateMany(NO_CHROMOSOMES);

        Fitness<MatrixChromosome> f1 = new CorrectFitness();
        Fitness<MatrixChromosome> f2 = new FastIntersectUnionFitness();

        long start = System.nanoTime();
        List<Double> scores1 = chromosomes.stream().map(f1::evaluate).toList();
        long end = System.nanoTime();
        double time1 = (end - start) / 1e6;
        start = System.nanoTime();
        List<Double> scores2 = chromosomes.stream().map(f2::evaluate).toList();
        end = System.nanoTime();
        double time2 = (end - start) / 1e6;

        System.out.println("CorrectFitness time for " + NO_CHROMOSOMES + " chromosomes: " + time1 + " ms");
        System.out.println("FastIntersectUnionFitness time for " + NO_CHROMOSOMES + " chromosomes: " + time2 + " ms");

        List<Double> abosoluteDiffs = new ArrayList<>();
        for (int i = 0; i < chromosomes.size(); i++) {
            double diff = Math.abs(scores1.get(i) - scores2.get(i));
            abosoluteDiffs.add(diff);
        }
        double averageAbsoluteError = abosoluteDiffs.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
        System.out.println("Average absolute error: " + averageAbsoluteError);
    }
}
