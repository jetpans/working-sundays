package project.models;

import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;

public class Global {
    public static final Random RANDOM = ThreadLocalRandom.current();
    public static final double MAX_RADIUS_OF_INFLUENCE = 5;
    public static final double MAX_CLUSTER_DISTANCE = 3;
    public static final double MAX_CLUSTER_JOIN_DISTANCE = 10;
}
