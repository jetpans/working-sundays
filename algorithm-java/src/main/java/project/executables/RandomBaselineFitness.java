package project.executables;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import project.genetic.chromosome.MatrixChromosome;
import project.genetic.fitness.FastIntersectUnionFitness;
import project.genetic.fitness.Fitness;
import project.genetic.generator.RandomGenerator;
import project.models.Global;
import project.models.Problem;
import project.settings.Settings;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

public class RandomBaselineFitness {

    public static void main(String[] args) {
        if (args.length < 1) {
            printUsageAndExit();
        }

        Path jobFolder = Path.of(args[0]);
        int samples = getIntArg(args, "--samples", 1000);
        long seed = getLongArg(args, "--seed", 0L);

        if (samples < 1) {
            System.err.println("--samples must be at least 1");
            System.exit(1);
        }

        Path dataPath = jobFolder.resolve("data.json");
        Path constraintsPath = jobFolder.resolve("constraints.json");
        Path descriptorPath = jobFolder.resolve("descriptor.job");
        Path solutionPath = jobFolder.resolve("results").resolve("solution.json");

        try {
            Problem.load(constraintsPath.toString(), dataPath.toString());
            Global.RANDOM = new Random(seed);

            Fitness<MatrixChromosome> fitness = new FastIntersectUnionFitness();
            if (Files.exists(descriptorPath)) {
                Settings<MatrixChromosome> settings = Settings.fromDescriptorJson(descriptorPath.toString());
                fitness = settings.fitness;
            }

            MatrixChromosome solution = loadSolution(solutionPath);
            double optimizedFitness = fitness.evaluate(solution);

            RandomGenerator generator = new RandomGenerator(Problem.getInstance().storeIds);
            List<Double> randomFitnesses = new ArrayList<>(samples);
            long startedMs = System.currentTimeMillis();
            for (int i = 0; i < samples; i++) {
                MatrixChromosome randomSolution = generator.generate();
                randomFitnesses.add(fitness.evaluate(randomSolution));
            }
            long elapsedMs = System.currentTimeMillis() - startedMs;

            Collections.sort(randomFitnesses);
            double mean = mean(randomFitnesses);
            double median = percentile(randomFitnesses, 50.0);
            double std = std(randomFitnesses, mean);
            double min = randomFitnesses.getFirst();
            double max = randomFitnesses.getLast();
            double p05 = percentile(randomFitnesses, 5.0);
            double p95 = percentile(randomFitnesses, 95.0);
            double optimizedPercentile = percentileRank(randomFitnesses, optimizedFitness);
            double improvement = optimizedFitness - mean;
            double improvementPct = mean == 0.0 ? 0.0 : improvement / Math.abs(mean) * 100.0;

            System.out.println("job_folder=" + jobFolder.toAbsolutePath());
            System.out.println("solution=" + solutionPath.toAbsolutePath());
            System.out.println("generator=RandomGenerator");
            System.out.println("fitness_class=" + fitness.getClass().getSimpleName());
            System.out.println("samples=" + samples);
            System.out.println("seed=" + seed);
            System.out.printf(Locale.US, "optimized_fitness=%.12f%n", optimizedFitness);
            System.out.printf(Locale.US, "random_mean=%.12f%n", mean);
            System.out.printf(Locale.US, "random_median=%.12f%n", median);
            System.out.printf(Locale.US, "random_std=%.12f%n", std);
            System.out.printf(Locale.US, "random_min=%.12f%n", min);
            System.out.printf(Locale.US, "random_p05=%.12f%n", p05);
            System.out.printf(Locale.US, "random_p95=%.12f%n", p95);
            System.out.printf(Locale.US, "random_max=%.12f%n", max);
            System.out.printf(Locale.US, "optimized_percentile=%.2f%n", optimizedPercentile);
            System.out.printf(Locale.US, "improvement_vs_mean=%.12f%n", improvement);
            System.out.printf(Locale.US, "improvement_vs_mean_pct=%.2f%n", improvementPct);
            System.out.printf(Locale.US, "elapsed_seconds=%.3f%n", elapsedMs / 1000.0);
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    private static MatrixChromosome loadSolution(Path solutionPath) throws Exception {
        MatrixChromosome chromosome = new MatrixChromosome(Problem.getInstance().storeIds);

        try (Reader reader = Files.newBufferedReader(solutionPath)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();

            for (int storeIndex = 0; storeIndex < chromosome.storeIds.size(); storeIndex++) {
                String storeId = chromosome.storeIds.get(storeIndex);
                JsonElement value = root.get(storeId);
                if (value == null || !value.isJsonArray()) {
                    System.err.println("Warning: solution missing store " + storeId);
                    continue;
                }

                List<Integer> model = new ArrayList<>();
                JsonArray sundays = value.getAsJsonArray();
                for (JsonElement sunday : sundays) {
                    model.add(sunday.getAsInt());
                }
                chromosome.setModel(storeIndex, model);
            }
        }

        return chromosome;
    }

    private static int getIntArg(String[] args, String name, int fallback) {
        String value = getArg(args, name);
        if (value == null) {
            return fallback;
        }
        return Integer.parseInt(value);
    }

    private static long getLongArg(String[] args, String name, long fallback) {
        String value = getArg(args, name);
        if (value == null) {
            return fallback;
        }
        return Long.parseLong(value);
    }

    private static String getArg(String[] args, String name) {
        for (int i = 1; i < args.length; i++) {
            if (!name.equals(args[i])) {
                continue;
            }
            if (i + 1 >= args.length) {
                throw new IllegalArgumentException("Missing value for " + name);
            }
            return args[i + 1];
        }
        return null;
    }

    private static double mean(List<Double> values) {
        double sum = 0.0;
        for (double value : values) {
            sum += value;
        }
        return sum / values.size();
    }

    private static double std(List<Double> values, double mean) {
        if (values.size() < 2) {
            return 0.0;
        }
        double sumSquared = 0.0;
        for (double value : values) {
            double delta = value - mean;
            sumSquared += delta * delta;
        }
        return Math.sqrt(sumSquared / (values.size() - 1));
    }

    private static double percentile(List<Double> sortedValues, double percentile) {
        if (sortedValues.isEmpty()) {
            return 0.0;
        }
        double position = percentile / 100.0 * (sortedValues.size() - 1);
        int lower = (int) Math.floor(position);
        int upper = (int) Math.ceil(position);
        if (lower == upper) {
            return sortedValues.get(lower);
        }
        double weight = position - lower;
        return sortedValues.get(lower) * (1.0 - weight) + sortedValues.get(upper) * weight;
    }

    private static double percentileRank(List<Double> sortedValues, double value) {
        if (sortedValues.isEmpty()) {
            return 0.0;
        }
        int lessOrEqual = 0;
        for (double sample : sortedValues) {
            if (sample <= value) {
                lessOrEqual++;
            }
        }
        return lessOrEqual * 100.0 / sortedValues.size();
    }

    private static void printUsageAndExit() {
        System.err.println("Usage: RandomBaselineFitness <jobFolder> [--samples N] [--seed SEED]");
        System.exit(1);
    }
}
