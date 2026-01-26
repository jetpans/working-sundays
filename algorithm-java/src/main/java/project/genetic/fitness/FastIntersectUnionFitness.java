package project.genetic.fitness;

import org.ejml.simple.SimpleMatrix;
import project.genetic.chromosome.MatrixChromosome;
import project.models.Problem;
import project.models.StoreData;

import java.util.Arrays;
import java.util.List;

public class FastIntersectUnionFitness implements Fitness<MatrixChromosome> {

    // Earth constants matching the Python implementation
    private static final double R_EARTH = 6371.0;
    private static final double LAT0 = Math.toRadians(45.10000);
    private static final double LON0 = Math.toRadians(15.2000);
    private static final double COS_LAT0 = Math.cos(LAT0);

    // Configurable constant

    public FastIntersectUnionFitness() {
    }

    @Override
    public double evaluate(MatrixChromosome c) {
        SimpleMatrix matrix = c.getWorksMatrix();
        int numStores = matrix.numRows();
        int numSundays = matrix.numCols();

        List<String> storeIds = c.storeIds;
        Problem problem = Problem.getInstance();

        // Pre-fetch store locations to avoid map lookups inside the loop
        // arrays are simpler/faster than lists for coordinate math
        double[] storeLats = new double[numStores];
        double[] storeLons = new double[numStores];

        for (int i = 0; i < numStores; i++) {
            StoreData sd = problem.data.storeDataMap.get(storeIds.get(i));
            // StoreData Point2D: x is longitude, y is latitude
            storeLons[i] = Math.toRadians(sd.location.x);
            storeLats[i] = Math.toRadians(sd.location.y);
        }

        // Project lat/lon to XY km once, as locations are static
        double[] storeX = new double[numStores];
        double[] storeY = new double[numStores];

        for (int i = 0; i < numStores; i++) {
            // formula: x = R * (lon - lon0) * cos(lat0)
            storeX[i] = R_EARTH * (storeLons[i] - LON0) * COS_LAT0;
            // formula: y = R * (lat - lat0)
            storeY[i] = R_EARTH * (storeLats[i] - LAT0);
        }

        double totalScore = 0.0;

        // Buffers for geometric calculation (reallocated per sunday if size changes,
        // but defined here to show scope)
        // We need arrays to store the box boundaries.
        // Size is at most numStores.
        double[] boxMinX = new double[numStores];
        double[] boxMinY = new double[numStores];
        double[] boxMaxX = new double[numStores];
        double[] boxMaxY = new double[numStores];

        for (int sunday = 0; sunday < numSundays; sunday++) {
            // 1. Calculate Sum of Weights for this Sunday

            // 2. Determine active boxes and their dimensions
            int activeCount = 0;

            for (int i = 0; i < numStores; i++) {
                double weight = matrix.get(i, sunday);
                if (weight > 0) {
                    double r = weight;

                    double x = storeX[i];
                    double y = storeY[i];

                    boxMinX[activeCount] = x - r;
                    boxMinY[activeCount] = y - r;
                    boxMaxX[activeCount] = x + r;
                    boxMaxY[activeCount] = y + r;
                    activeCount++;
                }
            }

            if (activeCount == 0) {
                continue; // No area for this Sunday
            }

            // 3. Calculate Union - Intersection Area
            // We pass only the filled portion of the arrays
            totalScore += calculateGridUnionMinusIntersect(activeCount, boxMinX, boxMinY, boxMaxX, boxMaxY);
        }

        return totalScore / numSundays;
    }

    /**
     * Calculates (UnionArea - IntersectionArea) using Coordinate Compression (Grid method).
     */
    private double calculateGridUnionMinusIntersect(int count, double[] bMinX, double[] bMinY, double[] bMaxX, double[] bMaxY) {
        // 1. Collect all unique X and Y coordinates to build the grid lines
        double[] xCoords = new double[count * 2];
        double[] yCoords = new double[count * 2];

        for (int i = 0; i < count; i++) {
            xCoords[2 * i] = bMinX[i];
            xCoords[2 * i + 1] = bMaxX[i];
            yCoords[2 * i] = bMinY[i];
            yCoords[2 * i + 1] = bMaxY[i];
        }

        // 2. Sort and remove duplicates to get unique grid lines
        xCoords = uniqueSort(xCoords);
        yCoords = uniqueSort(yCoords);

        int xLen = xCoords.length;
        int yLen = yCoords.length;

        if (xLen < 2 || yLen < 2) return 0.0;

        // 3. Grid Coverage Map
        // We use a flattened 1D array for the 2D grid of size (yLen-1) * (xLen-1)
        // grid[yIndex * (xLen - 1) + xIndex]
        int gridWidth = xLen - 1;
        int gridHeight = yLen - 1;
        int[] grid = new int[gridWidth * gridHeight];

        // 4. Fill the grid
        // For each box, find its range in xCoords and yCoords and increment grid cells
        for (int k = 0; k < count; k++) {
            // Binary search gives us the index in the sorted coordinate arrays
            // Since coords are exact matches from the input, result is always >= 0
            int xStart = Arrays.binarySearch(xCoords, bMinX[k]);
            int xEnd = Arrays.binarySearch(xCoords, bMaxX[k]);
            int yStart = Arrays.binarySearch(yCoords, bMinY[k]);
            int yEnd = Arrays.binarySearch(yCoords, bMaxY[k]);

            for (int y = yStart; y < yEnd; y++) {
                int rowOffset = y * gridWidth;
                for (int x = xStart; x < xEnd; x++) {
                    grid[rowOffset + x]++;
                }
            }
        }

        // 5. Compute Areas
        double unionArea = 0.0;
        double intersectArea = 0.0;

        for (int y = 0; y < gridHeight; y++) {
            double cellHeight = yCoords[y + 1] - yCoords[y];
            int rowOffset = y * gridWidth;

            for (int x = 0; x < gridWidth; x++) {
                int overlapCount = grid[rowOffset + x];

                if (overlapCount > 0) {
                    double cellArea = (xCoords[x + 1] - xCoords[x]) * cellHeight;

                    unionArea += cellArea;
                    if (overlapCount >= 2) {
                        intersectArea += cellArea;
                    }
                }
            }
        }

        return unionArea - intersectArea;
    }

    /**
     * Helper to sort an array and return a copy with only unique elements.
     */
    private double[] uniqueSort(double[] input) {
        Arrays.sort(input);
        int distinctCnt = 0;
        for (int i = 0; i < input.length; i++) {
            if (i == 0 || Double.compare(input[i], input[i - 1]) != 0) {
                distinctCnt++;
            }
        }

        double[] result = new double[distinctCnt];
        int pos = 0;
        for (int i = 0; i < input.length; i++) {
            if (i == 0 || Double.compare(input[i], input[i - 1]) != 0) {
                result[pos++] = input[i];
            }
        }
        return result;
    }
}