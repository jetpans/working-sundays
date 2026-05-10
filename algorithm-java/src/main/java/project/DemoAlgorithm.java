package project;

import project.genetic.chromosome.Chromosome;
import project.genetic.logger.LogLevel;
import project.settings.Settings;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class DemoAlgorithm<T extends Chromosome> {
    protected Settings<T> s;

    public DemoAlgorithm(Settings<T> settings) {
        this.s = settings;
    }

    public List<T> run() {
        List<T> population = s.generator.generateMany(s.populationSize); // New Population
        T alpha = null;
        population.forEach(chromosome -> chromosome.fitness = s.fitness.evaluate(chromosome)); // Give them fitness
        boolean lastWasAlpha = false;
        population.sort(Comparator.comparingDouble(a -> a.fitness)); // Order the first generation
        for (int iteration = 0; iteration < s.generations + 1; iteration++) { // Do an iteration
            List<T> nextPopulation = new ArrayList<>(population.subList(population.size() - s.elitism, population.size())); // Elite chromosomes survive
            while (nextPopulation.size() < s.populationSize - s.newChromosomes) { // Fill next population with children
                List<T> tempParents = s.selection.select(population); // Choose two parents.
                List<T> children = s.crossover.crossover(tempParents.getFirst(), tempParents.getLast()); // Get two children

                T first = children.getFirst();

                s.mutator.mutate(first); // Mutate first child
                first.fitness = s.fitness.evaluate(first); // Give fitness to first child
                nextPopulation.add(first); // Child in new generation

                if (nextPopulation.size() < s.populationSize - s.newChromosomes) {
                    T second = children.getLast();
                    s.mutator.mutate(second); // Mutate second child
                    second.fitness = s.fitness.evaluate(second); // Evaluate
                    nextPopulation.add(second); // Add
                }
            }
            for (int i = 0; i < s.newChromosomes; i++) { // Fill the rest with new chromosomes
                T newChromosome = s.generator.generate();
                newChromosome.fitness = s.fitness.evaluate(newChromosome);
                nextPopulation.add(newChromosome);
            }
            population = nextPopulation; // Assign next population
            population.sort(Comparator.comparingDouble(a -> a.fitness)); // Order the dudes


            if (iteration % 200 == 0) {
                s.logger.printf(LogLevel.VERBOSE, "\rIteration: " + iteration);
                lastWasAlpha = false;
            }

//            s.logger.println(LogLevel.DEBUG, "Last is " + population.getLast() + " with fitness of " + population.getLast().fitness);
            if (alpha == null || population.getLast().fitness > alpha.fitness) { // If we got new alpha, print that.
                alpha = population.getLast();
                if (!lastWasAlpha) {
                    s.logger.printf(LogLevel.VERBOSE, "\n");
                }
                lastWasAlpha = true;
                //alpha.exportToFile(String.format("%s%s%s_%.2f.txt", folderName, File.separator, iteration, alpha.fitness * 100));
                s.logger.println(LogLevel.VERBOSE, "New alpha has fitness of: " + alpha.fitness + " and looks like: " + alpha);
            }
        }

        s.logger.println(LogLevel.VERBOSE, "\n");
        return population;
    }
}
