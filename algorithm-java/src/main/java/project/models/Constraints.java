package project.models;

import java.util.Collections;
import java.util.List;

public class Constraints {
    public final List<Integer> works;
    public final List<Integer> free;

    public Constraints(List<Integer> works, List<Integer> free) {
        this.works = Collections.unmodifiableList(works);
        this.free = Collections.unmodifiableList(free);
    }
}
