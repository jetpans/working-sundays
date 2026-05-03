package project.models;

import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;

public class Global {
    public static final Random RANDOM = ThreadLocalRandom.current();
    public static double MAX_CLUSTER_DISTANCE = 3;
    public static double MAX_CLUSTER_JOIN_DISTANCE = 10;

    public static void applyClusterSettings(Double maxClusterDistance, Double maxClusterJoinDistance) {
        if (maxClusterDistance != null) {
            MAX_CLUSTER_DISTANCE = maxClusterDistance;
        }
        if (maxClusterJoinDistance != null) {
            MAX_CLUSTER_JOIN_DISTANCE = maxClusterJoinDistance;
        }
    }
}
