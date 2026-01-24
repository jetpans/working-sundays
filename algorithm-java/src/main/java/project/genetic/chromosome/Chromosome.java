package project.genetic.chromosome;


import java.util.List;

/**
 * Describes a unit used for algorithm
 */

public class Chromosome {

    public double fitness = Double.MIN_VALUE;
    public final List<String> storeIds;


    public Chromosome(List<String> storeIds) {
        this.storeIds = storeIds;
    }

    public Chromosome(Chromosome that) {
        this.storeIds = List.copyOf(that.storeIds);
    }


    public static Chromosome loadFromFile(String path) {
        throw new UnsupportedOperationException("Unimplemented method 'loadFromFile'");
    }

    public static Chromosome saveToFile(String path) {
        throw new UnsupportedOperationException("Unimplemented method 'saveToFile'");
    }

    @Override
    public String toString() {
        return "Chromosome{" +
                "fitness=" + fitness +
                '}';
    }

}
