package project.genetic.selection;

import project.genetic.chromosome.Chromosome;
import project.models.Global;

import java.util.ArrayList;
import java.util.List;

public class TournamentSelection implements Selection {
    private final int tournamentSize;

    public TournamentSelection(int tournamentSize) {
        this.tournamentSize = tournamentSize;
    }

    @Override
    public <T extends Chromosome> List<T> select(List<T> candidates) {
        List<T> choice = new ArrayList<>();
        for (int i = 0; i < tournamentSize; i++) {
            int randIndex = (int) (Global.RANDOM.nextDouble() * candidates.size());
            choice.add(candidates.get(randIndex));
        }
        choice.sort((a, b) -> Double.compare(b.fitness, a.fitness));
        return choice.subList(0, 2);
    }
}
