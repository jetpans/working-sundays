package project.models;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.awt.geom.Point2D;
import java.io.FileReader;
import java.io.IOException;
import java.io.Reader;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public class Data {


    public final Map<String, StoreData> storeDataMap;

    public Data(Map<String, StoreData> storeDataMap) {
        this.storeDataMap = storeDataMap;
    }

    public StoreData getStoreData(String storeId) {
        return storeDataMap.get(storeId);
    }


    /**
     * Loads store data from a JSON file.
     * Expected JSON structure: [{"node/123": { ...data... }}, {"way/456": { ...data... }}]
     */
    public static Data loadFromJson(String path) {
        Map<String, StoreData> map = new HashMap<>();

        // Define a default metric computer to use when loading data
        StoreData.MetricComputer defaultMetric = new StoreData.RatingCountMetric();

        try (Reader reader = new FileReader(path)) {
            // Parse the root as a JSON Element
            JsonElement rootElement = JsonParser.parseReader(reader);

            if (rootElement.isJsonArray()) {
                JsonArray jsonArray = rootElement.getAsJsonArray();

                // Iterate over the array elements
                for (JsonElement element : jsonArray) {
                    if (element.isJsonObject()) {
                        JsonObject obj = element.getAsJsonObject();
                        Set<Map.Entry<String, JsonElement>> entries = obj.entrySet();

                        // Iterate over the keys (e.g., "node/2162623568")
                        for (Map.Entry<String, JsonElement> entry : entries) {
                            String storeId = entry.getKey();
                            JsonObject details = entry.getValue().getAsJsonObject();

                            // Extract fields safely
                            String name = details.has("name") ? details.get("name").getAsString() : "Unknown";
                            String brand = details.has("brand") ? details.get("brand").getAsString() : null;
                            double rating = details.has("rating") ? details.get("rating").getAsDouble() : 0.0;
                            int ratingCount = details.has("user_ratings_total") ? details.get("user_ratings_total").getAsInt() : 0;
                            String address = details.has("formatted_address") ? details.get("formatted_address").getAsString() : "";

                            // Extract Coordinates
                            Point2D.Double location = null;
                            if (details.has("coordinates")) {
                                JsonArray coords = details.getAsJsonArray("coordinates");
                                if (coords.size() >= 2) {
                                    double lon = coords.get(0).getAsDouble();
                                    double lat = coords.get(1).getAsDouble();
                                    location = new Point2D.Double(lon, lat);
                                }
                            }

                            // Create StoreData instance
                            StoreData data = new StoreData(
                                    storeId,
                                    name,
                                    brand,
                                    rating,
                                    ratingCount,
                                    address,
                                    location,
                                    defaultMetric
                            );

                            map.put(storeId, data);
                        }
                    }
                }
            }
        } catch (IOException e) {
            System.err.println("Error reading JSON file: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to load store data from JSON.", e);
        }

        return new Data(map);
    }
}
