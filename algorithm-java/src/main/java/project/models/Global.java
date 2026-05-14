package project.models;

import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;

public class Global {
    public static Random RANDOM = new Random(0L);
    public static double MAX_CLUSTER_DISTANCE = 3;
    public static double MAX_CLUSTER_JOIN_DISTANCE = 10;

    public static void configureRandom(Boolean deterministic) {
        if (deterministic != null && !deterministic) {
            RANDOM = ThreadLocalRandom.current();
        } else {
            RANDOM = new Random(0L);
        }
    }

    public static void applyClusterSettings(Double maxClusterDistance, Double maxClusterJoinDistance) {
        if (maxClusterDistance != null) {
            MAX_CLUSTER_DISTANCE = maxClusterDistance;
        }
        if (maxClusterJoinDistance != null) {
            MAX_CLUSTER_JOIN_DISTANCE = maxClusterJoinDistance;
        }
    }
}
