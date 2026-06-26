package project.executables;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import project.genetic.chromosome.MatrixChromosome;
import project.genetic.fitness.FastIntersectUnionFitness;
import project.genetic.fitness.Fitness;
import project.models.Problem;
import project.models.StoreData;
import project.settings.Settings;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class EvaluateSolutionFitness {

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: EvaluateSolutionFitness <jobFolder>");
            System.exit(1);
        }

        Path jobFolder = Path.of(args[0]);
        Path dataPath = jobFolder.resolve("data.json");
        Path constraintsPath = jobFolder.resolve("constraints.json");
        Path descriptorPath = jobFolder.resolve("descriptor.job");
        Path solutionPath = jobFolder.resolve("results").resolve("solution.json");

        try {
            Problem.load(constraintsPath.toString(), dataPath.toString());

            Fitness<MatrixChromosome> fitness = new FastIntersectUnionFitness();
            if (Files.exists(descriptorPath)) {
                Settings<MatrixChromosome> settings = Settings.fromDescriptorJson(descriptorPath.toString());
                fitness = settings.fitness;
            }

            MatrixChromosome solution = loadSolution(solutionPath);
            solution.fitness = fitness.evaluate(solution);
            double directFitness = evaluateDirect(solutionPath);

            System.out.println("job_folder=" + jobFolder.toAbsolutePath());
            System.out.println("solution=" + solutionPath.toAbsolutePath());
            System.out.println("fitness_class=" + fitness.getClass().getSimpleName());
            System.out.printf("matrix_chromosome_fitness=%.12f%n", solution.fitness);
            System.out.printf("direct_solution_json_fitness=%.12f%n", directFitness);
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    private static MatrixChromosome loadSolution(Path solutionPath) throws Exception {
        MatrixChromosome chromosome = new MatrixChromosome(Problem.getInstance().storeIds);

        try (Reader reader = Files.newBufferedReader(solutionPath)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();

            for (int storeIndex = 0; storeIndex < chromosome.storeIds.size(); storeIndex++) {
                String storeId = chromosome.storeIds.get(storeIndex);
                JsonElement value = root.get(storeId);
                if (value == null || !value.isJsonArray()) {
                    System.err.println("Warning: solution missing store " + storeId);
                    continue;
                }

                List<Integer> model = new ArrayList<>();
                JsonArray sundays = value.getAsJsonArray();
                for (JsonElement sunday : sundays) {
                    model.add(sunday.getAsInt());
                }
                chromosome.setModel(storeIndex, model);
            }
        }

        return chromosome;
    }

    private static double evaluateDirect(Path solutionPath) throws Exception {
        Map<String, List<Integer>> solution = new LinkedHashMap<>();
        try (Reader reader = Files.newBufferedReader(solutionPath)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            for (Map.Entry<String, JsonElement> entry : root.entrySet()) {
                if (!entry.getValue().isJsonArray()) {
                    continue;
                }

                List<Integer> sundays = new ArrayList<>();
                for (JsonElement sunday : entry.getValue().getAsJsonArray()) {
                    sundays.add(sunday.getAsInt());
                }
                solution.put(entry.getKey(), sundays);
            }
        }

        Problem problem = Problem.getInstance();
        double totalScore = 0.0;
        for (int sunday = 0; sunday < problem.totalSundays; sunday++) {
            List<String> activeStoreIds = new ArrayList<>();
            for (Map.Entry<String, List<Integer>> entry : solution.entrySet()) {
                if (!problem.data.storeDataMap.containsKey(entry.getKey())) {
                    continue;
                }
                if (entry.getValue().contains(sunday)) {
                    activeStoreIds.add(entry.getKey());
                }
            }

            totalScore += evaluateSundayDirect(activeStoreIds);
        }

        return totalScore / problem.totalSundays;
    }

    private static double evaluateSundayDirect(List<String> activeStoreIds) {
        if (activeStoreIds.isEmpty()) {
            return 0.0;
        }

        final double rEarth = 6371.0;
        final double lat0 = Math.toRadians(45.10000);
        final double lon0 = Math.toRadians(15.2000);
        final double cosLat0 = Math.cos(lat0);

        int count = activeStoreIds.size();
        double[] minX = new double[count];
        double[] minY = new double[count];
        double[] maxX = new double[count];
        double[] maxY = new double[count];

        Problem problem = Problem.getInstance();
        for (int i = 0; i < count; i++) {
            StoreData store = problem.data.storeDataMap.get(activeStoreIds.get(i));
            double x = rEarth * (Math.toRadians(store.location.x) - lon0) * cosLat0;
            double y = rEarth * (Math.toRadians(store.location.y) - lat0);
            double radius = store.radius;
            minX[i] = x - radius;
            minY[i] = y - radius;
            maxX[i] = x + radius;
            maxY[i] = y + radius;
        }

        return calculateGridUnionMinusIntersect(count, minX, minY, maxX, maxY);
    }

    private static double calculateGridUnionMinusIntersect(int count, double[] bMinX, double[] bMinY, double[] bMaxX, double[] bMaxY) {
        double[] xCoords = new double[count * 2];
        double[] yCoords = new double[count * 2];

        for (int i = 0; i < count; i++) {
            xCoords[2 * i] = bMinX[i];
            xCoords[2 * i + 1] = bMaxX[i];
            yCoords[2 * i] = bMinY[i];
            yCoords[2 * i + 1] = bMaxY[i];
        }

        xCoords = uniqueSort(xCoords);
        yCoords = uniqueSort(yCoords);

        int gridWidth = xCoords.length - 1;
        int gridHeight = yCoords.length - 1;
        if (gridWidth < 1 || gridHeight < 1) {
            return 0.0;
        }

        int[] grid = new int[gridWidth * gridHeight];
        for (int k = 0; k < count; k++) {
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

    private static double[] uniqueSort(double[] input) {
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
