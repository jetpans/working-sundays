package project.genetic.generator;

import project.genetic.chromosome.MatrixChromosome;

import java.util.List;

public abstract class ForStoresGenerator implements Generator<MatrixChromosome> {
    public List<String> storeIds;

    public ForStoresGenerator(List<String> storeIds) {
        this.storeIds = storeIds;
    }


    public abstract ForStoresGenerator copyOf();
}
