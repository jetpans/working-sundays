package project.models;

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
     * Expected JSON structure:
     * {
     * "node/123": { ...data... },
     * "way/456": { ...data... }
     * }
     */
    public static Data loadFromJson(String path) {
        Map<String, StoreData> map = new HashMap<>();
        
        try (Reader reader = new FileReader(path)) {
            // Parse the root as a JSON Element
            JsonElement rootElement = JsonParser.parseReader(reader);

            // FIX: Check if root is a JSON Object (Map-like), not an Array
            if (rootElement.isJsonObject()) {
                JsonObject rootObj = rootElement.getAsJsonObject();

                // Get all entries (keys like "node/2162623568" and their values)
                Set<Map.Entry<String, JsonElement>> entries = rootObj.entrySet();

                for (Map.Entry<String, JsonElement> entry : entries) {
                    String storeId = entry.getKey();
                    JsonElement valueElement = entry.getValue();

                    if (valueElement.isJsonObject()) {
                        JsonObject details = valueElement.getAsJsonObject();

                        // Extract fields safely
                        String name = details.has("name") ? details.get("name").getAsString() : "Unknown";
                        String brand = details.has("brand") ? details.get("brand").getAsString() : null;
                        double rating = details.has("rating") ? details.get("rating").getAsDouble() : 0.0;
                        int ratingCount = details.has("user_ratings_total") ? details.get("user_ratings_total").getAsInt() : 0;
                        String address = details.has("formatted_address") ? details.get("formatted_address").getAsString() : "";
                        double radius = details.has("radius_km") ? details.get("radius_km").getAsDouble() : 0.0;

                        // Extract Coordinates
                        Point2D.Double location = null;
                        if (details.has("coordinates") && details.get("coordinates").isJsonArray()) {
                            var coords = details.getAsJsonArray("coordinates");
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
                                radius
                        );

                        map.put(storeId, data);
                    }
                }
            } else {
                System.err.println("JSON root is not an Object. Check file format.");
            }
        } catch (IOException e) {
            System.err.println("Error reading JSON file: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to load store data from JSON.", e);
        }

        System.out.println("Loaded " + map.size() + " store entries from " + path);
        return new Data(map);
    }
}