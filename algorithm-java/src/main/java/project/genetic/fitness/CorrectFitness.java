package project.genetic.fitness;

import org.ejml.simple.SimpleMatrix;
import org.locationtech.jts.geom.Envelope;
import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.operation.union.UnaryUnionOp;
import project.genetic.chromosome.MatrixChromosome;
import project.models.Problem;
import project.models.StoreData;

import java.util.ArrayList;
import java.util.List;

public class CorrectFitness implements Fitness<MatrixChromosome> {

    private static final double R_EARTH = 6371.0;
    private static final double LAT0 = Math.toRadians(45.10000);
    private static final double LON0 = Math.toRadians(15.2000);
    private static final double COS_LAT0 = Math.cos(LAT0);

    private final GeometryFactory geometryFactory;

    public CorrectFitness() {
        this.geometryFactory = new GeometryFactory();
    }

    @Override
    public double evaluate(MatrixChromosome c) {
        SimpleMatrix matrix = c.getWorksMatrix();
        int numStores = matrix.numRows();
        int numSundays = matrix.numCols();
        List<String> storeIds = c.storeIds;
        Problem problem = Problem.getInstance();

        // 1. Pre-calculate projected coordinates (Lat/Lon -> X/Y KM)
        // We use the same projection logic to ensure differences are only due to geometry calculation
        double[] storeX = new double[numStores];
        double[] storeY = new double[numStores];

        for (int i = 0; i < numStores; i++) {
            StoreData sd = problem.data.storeDataMap.get(storeIds.get(i));
            double latRad = Math.toRadians(sd.location.y);
            double lonRad = Math.toRadians(sd.location.x);

            storeX[i] = R_EARTH * (lonRad - LON0) * COS_LAT0;
            storeY[i] = R_EARTH * (latRad - LAT0);
        }

        double totalScore = 0.0;


        for (int sunday = 0; sunday < numSundays; sunday++) {
            // 2. Normalize column weights


            // 3. Create Boxes (Geometry)
            List<Geometry> currentSundayBoxes = new ArrayList<>();

            for (int i = 0; i < numStores; i++) {
                double val = matrix.get(i, sunday);
                if (val > 0) {
                    double radius = val;
                    double x = storeX[i];
                    double y = storeY[i];

                    // Create JTS Geometry (Polygon) from Envelope (Box)
                    Envelope envelope = new Envelope(x - radius, x + radius, y - radius, y + radius);
                    currentSundayBoxes.add(geometryFactory.toGeometry(envelope));
                }
            }

            if (currentSundayBoxes.isEmpty()) {
                continue;
            }

            // 4. Calculate Areas using JTS Set Operations
            // Python: union = unary_union(boxes)
            Geometry unionGeometry = UnaryUnionOp.union(currentSundayBoxes);
            double unionArea = unionGeometry.getArea();

            // Python: loop pairwise intersections
            List<Geometry> intersections = new ArrayList<>();
            for (int i = 0; i < currentSundayBoxes.size(); i++) {
                for (int j = i + 1; j < currentSundayBoxes.size(); j++) {
                    Geometry b1 = currentSundayBoxes.get(i);
                    Geometry b2 = currentSundayBoxes.get(j);

                    // Python: intersection = boxes[i].intersection(boxes[j])
                    Geometry intersection = b1.intersection(b2);

                    // Python: if not intersection.is_empty: intersects.append(...)
                    if (!intersection.isEmpty()) {
                        intersections.add(intersection);
                    }
                }
            }

            double intersectArea = 0.0;
            if (!intersections.isEmpty()) {
                // Python: intersect = unary_union(intersects)
                Geometry allIntersections = UnaryUnionOp.union(intersections);
                intersectArea = allIntersections.getArea();
            }

            totalScore += (unionArea - intersectArea);
        }

        return totalScore / numSundays;
    }
}