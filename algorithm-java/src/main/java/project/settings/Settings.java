package project.settings;

import project.genetic.chromosome.Chromosome;
import project.genetic.crossover.Crossover;
import project.genetic.fitness.Fitness;
import project.genetic.generator.Generator;
import project.genetic.logger.Logger;
import project.genetic.logger.SoutLogger;
import project.genetic.mutator.Mutator;
import project.genetic.selection.Selection;

import java.lang.reflect.InvocationTargetException;

public abstract class Settings<T extends Chromosome> {

    public String name;

    public int populationSize;
    public int generations;
    public int newChromosomes;
    public int elitism;

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
}
