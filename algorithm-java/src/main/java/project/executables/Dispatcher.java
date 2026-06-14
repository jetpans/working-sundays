package project.executables;

import project.DemoAlgorithm;
import project.Util;
import project.genetic.chromosome.MatrixChromosome;
import project.genetic.generator.AllSundaysHaveWorkGenerator;
import project.genetic.generator.ForStoresGenerator;
import project.genetic.generator.StochasticSeedingGenerator;
import project.models.Cluster;
import project.models.Global;
import project.models.Problem;
import project.settings.Settings;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class Dispatcher {

    public static void main(String[] args) {

        String instanceFolder = args[0];
        String dataPath = instanceFolder + "/data.json";
        String constraintPath = instanceFolder + "/constraints.json";
        Problem.load(constraintPath, dataPath);
        Settings<MatrixChromosome> settings = Settings.getSettings("project.settings.SmallRunSettings");
        Global.configureRandom(settings.deterministic);
        List<List<String>> clusters = Util.generateClusters(Problem.getInstance().storeIds, 3, Global.MAX_CLUSTER_DISTANCE, Global.RANDOM);

        List<Cluster> currentPool = new ArrayList<>();
        List<Cluster> solved = new ArrayList<>();
        for (List<String> clusterStoreIds : clusters) {
            currentPool.add(new Cluster(clusterStoreIds));
        }

        MatrixChromosome randomSol = new AllSundaysHaveWorkGenerator(Problem.getInstance().storeIds).generate();
        MatrixChromosome.toFile(randomSol, "D:\\Coding\\FAKS\\Mentor\\working-sundays\\results\\java\\random.sol");

        while (!currentPool.isEmpty()) {
            for (Cluster c : currentPool) {
                c.solution = solveSubProblem(settings, c.storeIds, c.seeds);
            }
            List<Cluster> nextPool = new ArrayList<>();

            while (!currentPool.isEmpty()) {
                Collections.shuffle(currentPool, Global.RANDOM);
                Cluster current = currentPool.removeFirst();
                Cluster bestMatch = null;
                double bestDistance = Double.MAX_VALUE;
                for (Cluster other : currentPool) {
                    double distance = Double.MAX_VALUE;
                    for (String storeIdA : current.storeIds) {
                        for (String storeIdB : other.storeIds) {
                            double d = Util.haversineDistance(Problem.getInstance().data.storeDataMap.get(storeIdA).location, Problem.getInstance().data.storeDataMap.get(storeIdB).location);
                            if (d < distance) {
                                distance = d;
                            }
                        }
                    }
                    if (distance < bestDistance) {
                        bestDistance = distance;
                        bestMatch = other;
                    }
                }

                if (bestMatch != null && bestDistance < Global.MAX_CLUSTER_JOIN_DISTANCE) {
                    // Merge clusters
                    currentPool.remove(bestMatch);
                    List<String> mergedStoreIds = new ArrayList<>(current.storeIds);
                    mergedStoreIds.addAll(bestMatch.storeIds);
                    Cluster mergedCluster = new Cluster(mergedStoreIds);
                    List<MatrixChromosome> existingSolutions = new ArrayList<>();
                    existingSolutions.add(current.solution);
                    existingSolutions.add(bestMatch.solution);
                    mergedCluster.solution = null;
                    mergedCluster.seeds = existingSolutions;
                    nextPool.add(mergedCluster);
                } else {
                    // Cannot merge, finalize this cluster
                    solved.add(current);
                }

            }
            currentPool = nextPool;
        }
        // Make directories
        storeFinalSolution(solved, "D:\\Coding\\FAKS\\Mentor\\working-sundays\\results\\java\\optimized.sol");
    }


    public static MatrixChromosome solveSubProblem(Settings subProblemSettings, List<String> storeIds, List<MatrixChromosome> existingSolutions) {
        if (!existingSolutions.isEmpty()) {
            subProblemSettings.generator = new StochasticSeedingGenerator(storeIds, existingSolutions, 0.8, subProblemSettings.generator);
        }
        subProblemSettings.generator = ((ForStoresGenerator) subProblemSettings.generator).copyOf();

        ((ForStoresGenerator) subProblemSettings.generator).storeIds = new ArrayList<>(storeIds);
        DemoAlgorithm<MatrixChromosome> algo = new DemoAlgorithm<>(subProblemSettings);
        return algo.run().getLast();
    }

    public static void storeFinalSolution(List<Cluster> solvedClusters, String outputPath) {
        List<String> finalStoreIds = new ArrayList<>();
        for (Cluster c : solvedClusters) {
            finalStoreIds.addAll(c.storeIds);
        }
        MatrixChromosome finalSolution = new MatrixChromosome(finalStoreIds);
        for (Cluster c : solvedClusters) {
            for (int i = 0; i < c.storeIds.size(); i++) {
                String storeId = c.storeIds.get(i);
                int finalIndex = finalSolution.storeIds.indexOf(storeId);
                finalSolution.setModel(finalIndex, new ArrayList<>(c.solution.getModel(i)));
            }
        }

        MatrixChromosome.toFile(finalSolution, outputPath);
    }
}
