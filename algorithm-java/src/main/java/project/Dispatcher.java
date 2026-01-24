package project;

import project.genetic.chromosome.MatrixChromosome;
import project.genetic.generator.SeedingGenerator;
import project.models.Global;
import project.models.Problem;
import project.settings.Settings;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class Dispatcher {

    public static void main(String[] args) {
        Problem.load(args[0], args[1]);
        Settings<MatrixChromosome> settings = Settings.getSettings("project.settings.DemoSettings");

        List<List<String>> clusters = Util.generateClusters(Problem.getInstance().storeIds, 5, 3, Global.RANDOM);

        List<Cluster> currentPool = new ArrayList<>();
        List<Cluster> solved = new ArrayList<>();
        for (List<String> clusterStoreIds : clusters) {
            currentPool.add(new Cluster(clusterStoreIds));
        }
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
                currentPool = nextPool;
            }
        }


    }

    public static class Cluster {
        public List<String> storeIds;
        public MatrixChromosome solution;
        public List<MatrixChromosome> seeds = new ArrayList<>();

        public Cluster(List<String> storeIds) {
            this.storeIds = storeIds;
        }
    }


    public static MatrixChromosome solveSubProblem(Settings subProblemSettings, List<String> storeIds, List<MatrixChromosome> existingSolutions) {
        if (!existingSolutions.isEmpty()) {
            subProblemSettings.generator = new SeedingGenerator(storeIds, existingSolutions, subProblemSettings.generator);
        }
        DemoAlgorithm<MatrixChromosome> algo = new DemoAlgorithm<>(subProblemSettings);
        return algo.run().getLast();
    }
}
