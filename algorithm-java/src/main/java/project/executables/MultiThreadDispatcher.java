package project.executables;

import project.Util;
import project.genetic.chromosome.MatrixChromosome;
import project.genetic.generator.AllSundaysHaveWorkGenerator;
import project.models.Cluster;
import project.models.Global;
import project.models.Problem;
import project.settings.Settings;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadPoolExecutor;

import static project.executables.Dispatcher.solveSubProblem;
import static project.executables.Dispatcher.storeFinalSolution;

public class MultiThreadDispatcher {

    public static void main(String[] args) {

        String instanceFolder = args[0];
        int numThreads = Integer.parseInt(args[1]);
        String dataPath = instanceFolder + "/data.json";
        String constraintPath = instanceFolder + "/constraints.json";
        Problem.load(constraintPath, dataPath);
        Settings<MatrixChromosome> settings = Settings.getSettings("project.settings.SmallRunSettings");
        List<List<String>> clusters = Util.generateClusters(Problem.getInstance().storeIds, 3, Global.MAX_CLUSTER_DISTANCE, Global.RANDOM);

        List<Cluster> currentPool = new ArrayList<>();
        List<Cluster> solved = new ArrayList<>();
        for (List<String> clusterStoreIds : clusters) {
            currentPool.add(new Cluster(clusterStoreIds));
        }

        MatrixChromosome randomSol = new AllSundaysHaveWorkGenerator(Problem.getInstance().storeIds).generate();
        MatrixChromosome.toFile(randomSol, "D:\\Coding\\FAKS\\Mentor\\working-sundays\\results\\java\\random.sol");

        ThreadPoolExecutor executor = (ThreadPoolExecutor) java.util.concurrent.Executors.newFixedThreadPool(numThreads);

        while (!currentPool.isEmpty()) {
//            for (Cluster c : currentPool) {
//                c.solution = solveSubProblem(settings, c.storeIds, c.seeds);
//            }
            List<Future<MatrixChromosome>> futures = new ArrayList<>();
            for (Cluster c : currentPool) {
                final Cluster cfinal = c;
                Future<MatrixChromosome> future = executor.submit(() -> solveSubProblem(Settings.copyOf(settings), cfinal.storeIds, cfinal.seeds));
                futures.add(future);
            }
            for (int i = 0; i < currentPool.size(); i++) {
                try {
                    MatrixChromosome solution = futures.get(i).get();
                    currentPool.get(i).solution = solution;
                } catch (Exception e) {
                    e.printStackTrace();
                    System.exit(-1);
                }
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
        executor.shutdown();
        storeFinalSolution(solved, "D:\\Coding\\FAKS\\Mentor\\working-sundays\\results\\java\\optimized.sol");
    }
}
