package project.executables;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import project.Util;
import project.genetic.chromosome.MatrixChromosome;
import project.genetic.generator.AllSundaysHaveWorkGenerator;
import project.models.Cluster;
import project.models.Global;
import project.models.Problem;
import project.settings.Settings;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadPoolExecutor;

import static project.executables.Dispatcher.solveSubProblem;
import static project.executables.Dispatcher.storeFinalSolution;

public class CallableDispatcher {

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: CallableDispatcher <instanceFolder> [numThreads]");
            System.exit(1);
        }

        String instanceFolder = args[0];
        String descriptorPath = instanceFolder + "/descriptor.job";
        String dataPath = instanceFolder + "/data.json";
        String constraintPath = instanceFolder + "/constraints.json";

        Problem.load(constraintPath, dataPath);
        Settings<MatrixChromosome> settings = Settings.fromDescriptorJson(descriptorPath);
        applyGlobalSettings(descriptorPath);

        // parse optional args: can include a --export-random flag and/or numThreads
        boolean exportRandom = false;
        int numThreads = settings.numThreads;
        for (int ai = 1; ai < args.length; ai++) {
            String a = args[ai];
            if ("--export-random".equals(a)) {
                exportRandom = true;
            } else {
                try {
                    numThreads = Integer.parseInt(a);
                } catch (NumberFormatException e) {
                    System.err.println("Unknown argument: " + a);
                }
            }
        }
        if (numThreads < 1) numThreads = 1;
        Global.configureRandom(settings.deterministic);

        List<List<String>> clusters = Util.generateClusters(
                Problem.getInstance().storeIds,
                3,
                Global.MAX_CLUSTER_DISTANCE,
                Global.RANDOM
        );

        List<Cluster> currentPool = new ArrayList<>();
        List<Cluster> solved = new ArrayList<>();
        for (List<String> clusterStoreIds : clusters) {
            currentPool.add(new Cluster(clusterStoreIds));
        }

        MatrixChromosome randomSol = new AllSundaysHaveWorkGenerator(Problem.getInstance().storeIds).generate();
        // write random solution only when requested; write into instance results folder
        try {
            Path resultsDir = Path.of(instanceFolder, "results");
            if (!resultsDir.toFile().exists()) resultsDir.toFile().mkdirs();
            if (exportRandom) {
                String randOut = Path.of(instanceFolder, "results", "random_start.json").toString();
                MatrixChromosome.toFile(randomSol, randOut);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        ThreadPoolExecutor executor = (ThreadPoolExecutor) java.util.concurrent.Executors.newFixedThreadPool(numThreads);

        while (!currentPool.isEmpty()) {
            List<Future<MatrixChromosome>> futures = new ArrayList<>();
            for (Cluster c : currentPool) {
                final Cluster cfinal = c;
                Future<MatrixChromosome> future = executor.submit(
                        () -> solveSubProblem(Settings.copyOf(settings), cfinal.storeIds, cfinal.seeds)
                );
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
                            double d = Util.haversineDistance(
                                    Problem.getInstance().data.storeDataMap.get(storeIdA).location,
                                    Problem.getInstance().data.storeDataMap.get(storeIdB).location
                            );
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
                    solved.add(current);
                }

            }
            currentPool = nextPool;
        }

        executor.shutdown();
        // store final optimized solution into instance results folder as solution.json
        try {
            Path resultsDir = Path.of(instanceFolder, "results");
            if (!resultsDir.toFile().exists()) resultsDir.toFile().mkdirs();
            String out = Path.of(instanceFolder, "results", "solution.json").toString();
            storeFinalSolution(solved, out);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static void applyGlobalSettings(String descriptorPath) {
        try (Reader reader = Files.newBufferedReader(Path.of(descriptorPath))) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            JsonObject settings = root.has("settings") ? root.getAsJsonObject("settings") : null;
            JsonObject general = settings != null && settings.has("general")
                    ? settings.getAsJsonObject("general")
                    : null;

            Double maxClusterDistance = null;
            Double maxClusterJoinDistance = null;

            if (general != null) {
                if (general.has("MAX_CLUSTER_DISTANCE")) {
                    maxClusterDistance = general.get("MAX_CLUSTER_DISTANCE").getAsDouble();
                }
                if (general.has("MAX_CLUSTER_JOIN_DISTANCE")) {
                    maxClusterJoinDistance = general.get("MAX_CLUSTER_JOIN_DISTANCE").getAsDouble();
                }
            }

            Global.applyClusterSettings(maxClusterDistance, maxClusterJoinDistance);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
