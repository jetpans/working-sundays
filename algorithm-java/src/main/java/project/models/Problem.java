package project.models;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.FileReader;
import java.io.IOException;
import java.io.Reader;
import java.util.*;

public class Problem {

    public final int workingSundays;
    public final int totalSundays;
    public final Map<String, Constraints> constraintsMap;
    public final List<String> storeIds;
    public final Data data;


    private static Problem instance;

    private Problem(int workingSundays, int totalSundays, Map<String, Constraints> constraintsMap, Data data) {
        this.workingSundays = workingSundays;
        this.totalSundays = totalSundays;
        this.constraintsMap = Collections.unmodifiableMap(constraintsMap);
        this.storeIds = List.copyOf(data.storeDataMap.keySet());
        this.data = data;
    }

    public static void create(int workingSundays, int totalSundays, Map<String, Constraints> constraintsMap, Data data) {
        if (instance == null) {
            instance = new Problem(workingSundays, totalSundays, constraintsMap, data);
        }
    }

    public static void load(String problemDefinitionPath, String dataPath) {
        // 1. Load the supporting Data object using its specific loader
        Data d = Data.loadFromJson(dataPath);

        int maxWorks = 0;
        int totalSundays = 0;
        Map<String, Constraints> parsedConstraints = new HashMap<>();

        try (Reader reader = new FileReader(problemDefinitionPath)) {
            // 2. Parse the root as a JSON Element
            JsonElement rootElement = JsonParser.parseReader(reader);

            if (rootElement.isJsonObject()) {
                JsonObject rootObj = rootElement.getAsJsonObject();
                Set<Map.Entry<String, JsonElement>> entries = rootObj.entrySet();

                // 3. First pass: Extract Global settings
                // We default to 0 if not found, similar to the safe extraction in your Data class
                if (rootObj.has("MAX_WORKS")) {
                    maxWorks = rootObj.get("MAX_WORKS").getAsInt();
                }
                if (rootObj.has("SUNDAYS")) {
                    totalSundays = rootObj.get("SUNDAYS").getAsInt();
                }

                // 4. Iterate over keys to find Store Constraints
                for (Map.Entry<String, JsonElement> entry : entries) {
                    String key = entry.getKey();

                    // Skip the global configuration keys
                    if (key.equals("YEAR") || key.equals("SUNDAYS") ||
                            key.equals("MAX_WORKS") || key.equals("MAX_DOESNT_WORK")) {
                        continue;
                    }

                    // Process dynamic keys (e.g., "relation/6308508")
                    if (entry.getValue().isJsonObject()) {
                        JsonObject constraintObj = entry.getValue().getAsJsonObject();
                        List<Integer> worksList = new ArrayList<>();
                        List<Integer> freeList = new ArrayList<>();

                        // Parse "works" array
                        if (constraintObj.has("works")) {
                            for (JsonElement val : constraintObj.getAsJsonArray("works")) {
                                worksList.add(val.getAsInt());
                            }
                        }

                        // Parse "doesnt_work" array (maps to 'free' in Constraints class)
                        if (constraintObj.has("doesnt_work")) {
                            for (JsonElement val : constraintObj.getAsJsonArray("doesnt_work")) {
                                freeList.add(val.getAsInt());
                            }
                        }

                        parsedConstraints.put(key, new Constraints(worksList, freeList));
                    }
                }
            }

            System.out.printf("Loaded Problem Definition: MAX_WORKS=%d, SUNDAYS=%d, Constraints for %d stores. Data for %d stores %n",
                    maxWorks, totalSundays, parsedConstraints.size(), d.storeDataMap.size());
            // 5. Create the singleton instance
            // Note: maxWorks maps to 'workingSundays' in the constructor based on context
            instance = new Problem(maxWorks, totalSundays, parsedConstraints, d);

        } catch (IOException e) {
            System.err.println("Error reading Problem Definition JSON: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to load problem definition.", e);
        }
    }

    public static Problem getInstance() {
        if (instance == null) {
            throw new IllegalStateException("Problem instance not created yet.");
        }
        return instance;
    }
}
