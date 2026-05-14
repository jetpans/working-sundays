package project.settings;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import project.genetic.chromosome.Chromosome;
import project.genetic.chromosome.MatrixChromosome;
import project.genetic.crossover.ColumnKSwitchCrossover;
import project.genetic.crossover.CompositeCrossover;
import project.genetic.crossover.Crossover;
import project.genetic.crossover.GeometricColumnCrossover;
import project.genetic.crossover.GeometricRowCrossover;
import project.genetic.crossover.KSwitchCrossover;
import project.genetic.crossover.SinglePointCrossover;
import project.genetic.fitness.CorrectFitness;
import project.genetic.fitness.FastIntersectUnionFitness;
import project.genetic.fitness.Fitness;
import project.genetic.generator.AllSundaysHaveWorkGenerator;
import project.genetic.generator.CompositeGenerator;
import project.genetic.generator.Generator;
import project.genetic.generator.RandomGenerator;
import project.genetic.generator.SeedingGenerator;
import project.genetic.logger.Logger;
import project.genetic.logger.SoutLogger;
import project.genetic.mutator.CompositeMutator;
import project.genetic.mutator.Mutator;
import project.genetic.mutator.RandomSimpleMutator;
import project.genetic.selection.RankSelection;
import project.genetic.selection.Selection;
import project.genetic.selection.TournamentSelection;

import java.io.Reader;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public abstract class Settings<T extends Chromosome> {

    public String name;

    public int populationSize;
    public int generations;
    public int newChromosomes;
    public int elitism;
    public int numThreads = 4;
    public boolean deterministic = true;

    public Mutator<T> mutator;
    public Crossover<T> crossover;
    public Selection selection;
    public Fitness<T> fitness;
    public Generator<T> generator;
    public Logger logger = new SoutLogger();


    public static Settings getSettings(String name) {
        try {
            Class<?> clazz = Class.forName(name);
            Settings settingsInstance = (Settings) clazz.getDeclaredConstructor().newInstance();
            return settingsInstance; // Call a method on the instance
        } catch (ClassNotFoundException | InstantiationException | IllegalAccessException | NoSuchMethodException |
                 InvocationTargetException e) {
            e.printStackTrace();
            System.exit(-1);
            return null;
        }
    }

    public static Settings copyOf(Settings other) {
        Settings copy;
        try {
            copy = other.getClass().getDeclaredConstructor().newInstance();
            copy.name = other.name;
            copy.populationSize = other.populationSize;
            copy.generations = other.generations;
            copy.newChromosomes = other.newChromosomes;
            copy.elitism = other.elitism;
            copy.numThreads = other.numThreads;
            copy.deterministic = other.deterministic;
            copy.mutator = other.mutator;
            copy.crossover = other.crossover;
            copy.selection = other.selection;
            copy.fitness = other.fitness;
            copy.generator = other.generator;
            copy.logger = other.logger;
            return copy;
        } catch (InstantiationException | IllegalAccessException | NoSuchMethodException |
                 InvocationTargetException e) {
            e.printStackTrace();
            throw new RuntimeException("Failed to copy Settings instance.", e);
        }
    }

    public static Settings<MatrixChromosome> fromDescriptorJson(String descriptorPath) {
        Settings<MatrixChromosome> settings = Settings.getSettings("project.settings.SmallRunSettings");

        try (Reader reader = Files.newBufferedReader(Path.of(descriptorPath))) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            JsonObject settingsObj = getObject(root, "settings");
            if (settingsObj == null) {
                return settings;
            }

            JsonObject ga = getObject(settingsObj, "ga");
            if (ga == null) {
                return settings;
            }

            settings.populationSize = getInt(ga, "populationSize", settings.populationSize);
            settings.generations = getInt(ga, "generations", settings.generations);
            settings.newChromosomes = getInt(ga, "newChromosomes", settings.newChromosomes);
            settings.elitism = getInt(ga, "elitism", settings.elitism);
            settings.numThreads = getInt(ga, "numThreads", settings.numThreads);
            settings.deterministic = getBoolean(ga, "deterministic", settings.deterministic);

            settings.mutator = buildMutator(getObject(ga, "mutator"), settings.mutator);
            settings.crossover = buildCrossover(getObject(ga, "crossover"), settings.crossover);
            settings.selection = buildSelection(getObject(ga, "selection"), settings.selection);
            settings.fitness = buildFitness(getObject(ga, "fitness"), settings.fitness);
            settings.generator = buildGenerator(getObject(ga, "generator"), settings.generator);
            settings.logger = buildLogger(getObject(ga, "logger"), settings.logger);
        } catch (Exception e) {
            e.printStackTrace();
        }

        return settings;
    }

    private static Mutator<MatrixChromosome> buildMutator(JsonObject obj, Mutator<MatrixChromosome> fallback) {
        if (obj == null) return fallback;
        String type = getString(obj, "type", "");
        JsonObject params = getObject(obj, "params");

        if ("RandomSimpleMutator".equals(type)) {
            int numMutations = getInt(params, "numMutations", 5);
            double p = getDouble(params, "p", 0.5);
            return new RandomSimpleMutator(numMutations, p);
        }

        if ("CompositeMutator".equals(type)) {
            double p = getDouble(params, "p", 1.0);
            CompositeBuild<Mutator<MatrixChromosome>> children = buildMutatorChildren(params);
            if (children.items.isEmpty()) return fallback;
            return new CompositeMutator<>(p, children.items, children.weights);
        }

        return fallback;
    }

    private static CompositeBuild<Mutator<MatrixChromosome>> buildMutatorChildren(JsonObject params) {
        CompositeBuild<Mutator<MatrixChromosome>> out = new CompositeBuild<>();
        JsonArray children = getArray(params, "children");
        if (children == null) return out;

        for (JsonElement childElem : children) {
            JsonObject childObj = childElem.getAsJsonObject();
            Mutator<MatrixChromosome> child = buildMutator(childObj, null);
            if (child == null) continue;
            out.items.add(child);
            out.weightsList.add(getDouble(childObj, "weight", 1.0));
        }
        out.finalizeWeights();
        return out;
    }

    private static Crossover<MatrixChromosome> buildCrossover(JsonObject obj, Crossover<MatrixChromosome> fallback) {
        if (obj == null) return fallback;
        String type = getString(obj, "type", "");
        JsonObject params = getObject(obj, "params");

        if ("GeometricColumnCrossover".equals(type)) {
            double geoP = getDouble(params, "geoP", 0.3);
            double crossoverProb = getDouble(params, "crossoverProb", 0.7);
            return new GeometricColumnCrossover(geoP, crossoverProb);
        }

        if ("GeometricRowCrossover".equals(type)) {
            double geoP = getDouble(params, "geoP", 0.3);
            double crossoverProb = getDouble(params, "crossoverProb", 0.7);
            return new GeometricRowCrossover(geoP, crossoverProb);
        }

        if ("SinglePointCrossover".equals(type)) {
            double p = getDouble(params, "p", 0.5);
            return new SinglePointCrossover(p);
        }

        if ("KSwitchCrossover".equals(type)) {
            int k = getInt(params, "k", 3);
            double p = getDouble(params, "p", 0.5);
            return new KSwitchCrossover(k, p);
        }

        if ("ColumnKSwitchCrossover".equals(type)) {
            int k = getInt(params, "k", 3);
            double p = getDouble(params, "p", 0.5);
            return new ColumnKSwitchCrossover(k, p);
        }

        if ("CompositeCrossover".equals(type)) {
            double p = getDouble(params, "p", 1.0);
            CompositeBuild<Crossover<MatrixChromosome>> children = buildCrossoverChildren(params);
            if (children.items.isEmpty()) return fallback;
            return new CompositeCrossover<>(p, children.items, children.weights);
        }

        return fallback;
    }

    private static CompositeBuild<Crossover<MatrixChromosome>> buildCrossoverChildren(JsonObject params) {
        CompositeBuild<Crossover<MatrixChromosome>> out = new CompositeBuild<>();
        JsonArray children = getArray(params, "children");
        if (children == null) return out;

        for (JsonElement childElem : children) {
            JsonObject childObj = childElem.getAsJsonObject();
            Crossover<MatrixChromosome> child = buildCrossover(childObj, null);
            if (child == null) continue;
            out.items.add(child);
            out.weightsList.add(getDouble(childObj, "weight", 1.0));
        }
        out.finalizeWeights();
        return out;
    }

    private static Selection buildSelection(JsonObject obj, Selection fallback) {
        if (obj == null) return fallback;
        String type = getString(obj, "type", "");
        JsonObject params = getObject(obj, "params");

        if ("TournamentSelection".equals(type)) {
            int tournamentSize = getInt(params, "tournamentSize", 3);
            return new TournamentSelection(tournamentSize);
        }

        if ("RankSelection".equals(type)) {
            return new RankSelection();
        }

        return fallback;
    }

    private static Fitness<MatrixChromosome> buildFitness(JsonObject obj, Fitness<MatrixChromosome> fallback) {
        if (obj == null) return fallback;
        String type = getString(obj, "type", "");

        if ("FastIntersectUnionFitness".equals(type)) {
            return new FastIntersectUnionFitness();
        }

        if ("CorrectFitness".equals(type)) {
            return new CorrectFitness();
        }

        return fallback;
    }

    private static Generator<MatrixChromosome> buildGenerator(JsonObject obj, Generator<MatrixChromosome> fallback) {
        if (obj == null) return fallback;
        String type = getString(obj, "type", "");
        JsonObject params = getObject(obj, "params");

        if ("AllSundaysHaveWorkGenerator".equals(type)) {
            return new AllSundaysHaveWorkGenerator(new ArrayList<>());
        }

        if ("RandomGenerator".equals(type)) {
            return new RandomGenerator(new ArrayList<>());
        }

        if ("SeedingGenerator".equals(type)) {
            Generator<MatrixChromosome> fallbackGen = new AllSundaysHaveWorkGenerator(new ArrayList<>());
            return new SeedingGenerator(new ArrayList<>(), new ArrayList<>(), fallbackGen);
        }

        if ("CompositeGenerator".equals(type)) {
            CompositeBuild<Generator<MatrixChromosome>> children = buildGeneratorChildren(params);
            if (children.items.isEmpty()) return fallback;
            return new CompositeGenerator<>(children.items, children.weights);
        }

        return fallback;
    }

    private static CompositeBuild<Generator<MatrixChromosome>> buildGeneratorChildren(JsonObject params) {
        CompositeBuild<Generator<MatrixChromosome>> out = new CompositeBuild<>();
        JsonArray children = getArray(params, "children");
        if (children == null) return out;

        for (JsonElement childElem : children) {
            JsonObject childObj = childElem.getAsJsonObject();
            Generator<MatrixChromosome> child = buildGenerator(childObj, null);
            if (child == null) continue;
            out.items.add(child);
            out.weightsList.add(getDouble(childObj, "weight", 1.0));
        }
        out.finalizeWeights();
        return out;
    }

    private static Logger buildLogger(JsonObject obj, Logger fallback) {
        if (obj == null) return fallback;
        String type = getString(obj, "type", "");

        if ("SoutLogger".equals(type)) {
            return new SoutLogger();
        }

        return fallback;
    }

    private static String getString(JsonObject obj, String key, String fallback) {
        if (obj == null || !obj.has(key)) return fallback;
        try {
            return obj.get(key).getAsString();
        } catch (Exception e) {
            return fallback;
        }
    }

    private static int getInt(JsonObject obj, String key, int fallback) {
        if (obj == null || !obj.has(key)) return fallback;
        try {
            return obj.get(key).getAsInt();
        } catch (Exception e) {
            return fallback;
        }
    }

    private static double getDouble(JsonObject obj, String key, double fallback) {
        if (obj == null || !obj.has(key)) return fallback;
        try {
            return obj.get(key).getAsDouble();
        } catch (Exception e) {
            return fallback;
        }
    }

    private static boolean getBoolean(JsonObject obj, String key, boolean fallback) {
        if (obj == null || !obj.has(key)) return fallback;
        try {
            return obj.get(key).getAsBoolean();
        } catch (Exception e) {
            return fallback;
        }
    }

    private static JsonObject getObject(JsonObject obj, String key) {
        if (obj == null || !obj.has(key)) return null;
        try {
            return obj.getAsJsonObject(key);
        } catch (Exception e) {
            return null;
        }
    }

    private static JsonArray getArray(JsonObject obj, String key) {
        if (obj == null || !obj.has(key)) return null;
        try {
            return obj.getAsJsonArray(key);
        } catch (Exception e) {
            return null;
        }
    }

    private static class CompositeBuild<T> {
        private final List<T> items = new ArrayList<>();
        private final List<Double> weightsList = new ArrayList<>();
        private double[] weights = new double[0];

        private void finalizeWeights() {
            weights = new double[weightsList.size()];
            for (int i = 0; i < weightsList.size(); i++) {
                weights[i] = weightsList.get(i);
            }
        }
    }
}
