package project.genetic.selection;

import project.genetic.chromosome.Chromosome;
import project.models.Global;

import java.util.ArrayList;
import java.util.List;

public class RankSelection implements Selection {
    List<Double> probabilities;

    @Override
    public <T extends Chromosome> List<T> select(List<T> candidates) {
//        candidates.sort((a, b) -> Double.compare(b.fitness, a.fitness));
        if (probabilities == null || probabilities.size() != candidates.size()) {
            probabilities = new ArrayList<>();
            int n = candidates.size();
            double totalRank = n * (n + 1) / 2.0;
            for (int i = 0; i < n; i++) {
                probabilities.add((i) / totalRank);
            }
        }
        double r1 = Global.RANDOM.nextDouble();
        double r2 = Global.RANDOM.nextDouble();
        if (r1 > r2) {
            double temp = r1;
            r1 = r2;
            r2 = temp;
        }

        for (int i = 0; i < candidates.size(); i++) {
            r1 -= probabilities.get(i);
            if (r1 <= 0) {
                for (int j = i; j < candidates.size(); j++) {
                    r2 -= probabilities.get(j);
                    if (r2 <= 0) {
                        return List.of(candidates.get(i), candidates.get(j));
                    }
                }
            }
        }
        return List.of(candidates.getFirst(), candidates.get(1));
    }
}
