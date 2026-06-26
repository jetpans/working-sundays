package project.genetic.logger;

import project.genetic.chromosome.Chromosome;
import project.genetic.chromosome.MatrixChromosome;
import project.genetic.fitness.Fitness;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class FitnessHistoryLogger extends SoutLogger {

    private final MatrixChromosome prototype;
    private final Fitness<MatrixChromosome> fitness;
    private final Path outputPath;
    private final long startMs;

    private MatrixChromosome bestPrototype;
    private double bestGlobalFitness = Double.NEGATIVE_INFINITY;

    public FitnessHistoryLogger(MatrixChromosome prototype, Fitness<MatrixChromosome> fitness, Path outputPath) {
        super();
        this.prototype = prototype;
        this.fitness = fitness;
        this.outputPath = outputPath;
        this.startMs = System.currentTimeMillis();

        try {
            Path parent = outputPath.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Files.writeString(
                    outputPath,
                    "timestamp_ms,elapsed_ms,iteration,incoming_alpha_fitness,global_fitness,best_global_fitness\n",
                    StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE,
                    StandardOpenOption.TRUNCATE_EXISTING
            );
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public synchronized void logAlpha(int iteration, Chromosome alpha) {
        if (!(alpha instanceof MatrixChromosome incomingAlpha)) {
            return;
        }

        copyModelRows(incomingAlpha);

        double globalFitness = fitness.evaluate(prototype);
        if (globalFitness > bestGlobalFitness) {
            bestGlobalFitness = globalFitness;
            bestPrototype = new MatrixChromosome(prototype);
            bestPrototype.fitness = globalFitness;
        }

        appendHistoryRow(iteration, incomingAlpha.fitness, globalFitness);
    }

    public synchronized MatrixChromosome getBestPrototype() {
        if (bestPrototype == null) {
            return null;
        }
        MatrixChromosome copy = new MatrixChromosome(bestPrototype);
        copy.fitness = bestGlobalFitness;
        return copy;
    }

    public synchronized double getBestGlobalFitness() {
        return bestGlobalFitness;
    }

    private void copyModelRows(MatrixChromosome incomingAlpha) {
        for (int incomingIndex = 0; incomingIndex < incomingAlpha.storeIds.size(); incomingIndex++) {
            String storeId = incomingAlpha.storeIds.get(incomingIndex);
            int prototypeIndex = prototype.storeIds.indexOf(storeId);
            if (prototypeIndex < 0) {
                continue;
            }

            List<Integer> modelRow = new ArrayList<>(incomingAlpha.getModel(incomingIndex));
            prototype.setModel(prototypeIndex, modelRow);
        }
    }

    private void appendHistoryRow(int iteration, double incomingAlphaFitness, double globalFitness) {
        long timestampMs = System.currentTimeMillis();
        long elapsedMs = timestampMs - startMs;
        String row = String.format(
                Locale.US,
                "%d,%d,%d,%.12f,%.12f,%.12f%n",
                timestampMs,
                elapsedMs,
                iteration,
                incomingAlphaFitness,
                globalFitness,
                bestGlobalFitness
        );

        try {
            Files.writeString(
                    outputPath,
                    row,
                    StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE,
                    StandardOpenOption.APPEND
            );
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
