package project;

import project.models.Problem;
import project.models.StoreData;

import java.awt.geom.Point2D;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class Util {

    public static double haversineDistance(Point2D p1, Point2D p2) {
        final double R = 6371.0; // Earth radius in kilometers
        double lat1 = Math.toRadians(p1.getY());
        double lon1 = Math.toRadians(p1.getX());
        double lat2 = Math.toRadians(p2.getY());
        double lon2 = Math.toRadians(p2.getX());

        double dLat = lat2 - lat1;
        double dLon = lon2 - lon1;

        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(lat1) * Math.cos(lat2) *
                        Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

        return R * c; // Distance in kilometers
    }

    public static Point2D projectToXY(Point2D lonLat) {
        final double R_EARTH = 6371.0;
        final double LAT0 = Math.toRadians(45.10000);
        final double LON0 = Math.toRadians(15.2000);
        final double COS_LAT0 = Math.cos(LAT0);

        double latRad = Math.toRadians(lonLat.getY());
        double lonRad = Math.toRadians(lonLat.getX());

        double x = R_EARTH * (lonRad - LON0) * COS_LAT0;
        double y = R_EARTH * (latRad - LAT0);

        return new Point2D.Double(x, y);
    }

    public static List<List<String>> generateClusters(List<String> storeIds, int maxClusterSize, double maxDistance, Random r) {
        List<StoreData> stores = new ArrayList<>(storeIds.stream()
                .map(id -> Problem.getInstance().data.storeDataMap.get(id))
                .toList());

        List<List<String>> clusters = new ArrayList<>();

        while (!stores.isEmpty()) {
            StoreData current = stores.remove(r.nextInt(stores.size()));
            int closestClusterIndex = -1;
            double closestDistance = Double.MAX_VALUE;
            for (int i = 0; i < clusters.size(); i++) {
                List<String> cluster = clusters.get(i);
                if (cluster.size() >= maxClusterSize) continue;
                double closestDistanceInCluster = Double.MAX_VALUE;
                for (String storeId : cluster) {
                    StoreData sd = Problem.getInstance().data.storeDataMap.get(storeId);
                    double d = haversineDistance(current.location, sd.location);
                    closestDistanceInCluster = Math.min(closestDistanceInCluster, d);
                }
                if (closestDistanceInCluster > maxDistance) continue;

                if (closestDistanceInCluster < closestDistance) {
                    closestDistance = closestDistanceInCluster;
                    closestClusterIndex = i;
                }
            }
            if (closestClusterIndex == -1) {
                List<String> newCluster = new ArrayList<>();
                newCluster.add(current.storeId);
                clusters.add(newCluster);
            } else {
                clusters.get(closestClusterIndex).add(current.storeId);
            }
        }
        return clusters;
    }

    public static int randomGeometric(int max, double p, Random r) {
        double d = r.nextDouble();
        int result = (int) Math.floor(Math.log(1.0 - d) / Math.log(1.0 - p));
        return Math.min(result, max);
    }
}
