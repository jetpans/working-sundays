package project.models;

import java.awt.geom.Point2D;

public class StoreData {

    public final String storeId;
    public final String name;
    public final String brand;
    public final double rating;
    public final int ratingCount;
    public final String formattedAddress;
    public final Point2D.Double location;
    public double radius;


    public StoreData(String storeId, String name, String brand, double rating, int ratingCount, String formattedAddress, Point2D.Double location, double radius) {
        this.storeId = storeId;
        this.name = name;
        this.brand = brand;
        this.rating = rating;
        this.ratingCount = ratingCount;
        this.formattedAddress = formattedAddress;
        this.location = location;
        this.radius = radius;
    }

    @Override
    public int hashCode() {
        return storeId.hashCode();
    }

}
