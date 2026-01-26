package project.models;

import project.genetic.chromosome.MatrixChromosome;

import java.util.ArrayList;
import java.util.List;

public class Cluster {
    public List<String> storeIds;
    public MatrixChromosome solution;
    public List<MatrixChromosome> seeds = new ArrayList<>();

    public Cluster(List<String> storeIds) {
        this.storeIds = storeIds;
    }
}