package project.genetic.chromosome;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import org.ejml.simple.SimpleMatrix;
import project.models.Constraints;
import project.models.Problem;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class MatrixChromosome extends Chromosome {
    private final List<List<Integer>> works;
    private List<List<Integer>> model;
    private List<List<Integer>> antiModel;
    private final List<Constraints> constraints;
    private SimpleMatrix worksMatrix;

    public MatrixChromosome(List<String> storeIds) {
        super(storeIds);
        this.works = new ArrayList<>();
        this.antiModel = new ArrayList<>();
        this.model = new ArrayList<>();
        this.constraints = new ArrayList<>();

        this.worksMatrix = new SimpleMatrix(storeIds.size(), Problem.getInstance().totalSundays);

        Problem p = Problem.getInstance();
        for (String id : storeIds) {
            Constraints c = p.constraintsMap.get(id);
            this.constraints.add(c);
            this.works.add(c.works);
            for (int i : c.works) {
                this.worksMatrix.set(this.works.size() - 1, i, p.data.storeDataMap.get(id).radius);
            }
            this.antiModel.add(new ArrayList<>());
            this.model.add(new ArrayList<>());
            for (int i = 0; i < p.totalSundays; i++) {
                if (!c.works.contains(i) && !c.free.contains(i)) {
                    this.antiModel.getLast().add(i);
                }
            }
        }
    }

    public MatrixChromosome(MatrixChromosome that) {
        super(that);


        this.works = that.works;

        this.constraints = that.constraints;

        this.worksMatrix = that.worksMatrix.copy();

        this.model = new ArrayList<>(that.model.size());
        for (List<Integer> row : that.model) {
            this.model.add(new ArrayList<>(row));
        }

        this.antiModel = new ArrayList<>(that.antiModel.size());
        for (List<Integer> row : that.antiModel) {
            this.antiModel.add(new ArrayList<>(row));
        }
    }

    public SimpleMatrix getWorksMatrix() {
        return worksMatrix;
    }

    public List<List<Integer>> getModel() {
        return model;
    }

    public List<List<Integer>> getWorks() {
        return works;
    }

    public List<List<Integer>> getAntiModel() {
        return antiModel;
    }

    public List<Integer> getModel(int storeIndex) {
        return model.get(storeIndex);
    }

    public List<Integer> getAntiModel(int storeIndex) {
        return antiModel.get(storeIndex);
    }

    public List<Integer> getWorks(int storeIndex) {
        return works.get(storeIndex);
    }


    public void fromModelToAntiModel(int storeIndex, int index) {
        Integer s = this.model.get(storeIndex).remove(index);
        this.antiModel.get(storeIndex).add(s);
        this.worksMatrix.set(storeIndex, s, 0);
    }

    public void fromAntiModelToModel(int storeIndex, int index) {
        Integer s = this.antiModel.get(storeIndex).remove(index);
        this.model.get(storeIndex).add(s);
        this.worksMatrix.set(storeIndex, s, Problem.getInstance().data.storeDataMap.get(super.storeIds.get(storeIndex)).radius);
    }

    public void moveToModel(int storeIndex, int sunday) {
        this.antiModel.get(storeIndex).remove((Integer) sunday);
        this.model.get(storeIndex).add(sunday);
        this.worksMatrix.set(storeIndex, sunday, Problem.getInstance().data.storeDataMap.get(super.storeIds.get(storeIndex)).radius);
    }

    public void removeFromModel(int storeIndex, int sunday) {
        this.model.get(storeIndex).remove((Integer) sunday);
        this.antiModel.get(storeIndex).add(sunday);
        this.worksMatrix.set(storeIndex, sunday, 0);
    }


    public void setModel(int storeIndex, List<Integer> newModel) {
        for (Integer s : this.model.get(storeIndex)) {
            this.worksMatrix.set(storeIndex, s, 0);
        }
        this.model.get(storeIndex).clear();
        this.antiModel.get(storeIndex).clear();

        Constraints c = this.constraints.get(storeIndex);
        for (int i = 0; i < Problem.getInstance().totalSundays; i++) {
            if (c.works.contains(i)) {
                continue; // Skip fixed works
            }
            if (newModel.contains(i)) {
                this.model.get(storeIndex).add(i);
                this.worksMatrix.set(storeIndex, i, Problem.getInstance().data.storeDataMap.get(super.storeIds.get(storeIndex)).radius);
            } else if (!c.free.contains(i)) {
                this.antiModel.get(storeIndex).add(i);
            }
        }
    }

    public static void toFile(MatrixChromosome chromosome, String filename) {
        JsonObject root = new JsonObject();

        // Iterate through all stores
        // We assume storeIds, works, and model are all aligned by index
        for (int i = 0; i < chromosome.storeIds.size(); i++) {
            String storeId = chromosome.storeIds.get(i);
            JsonArray sundays = new JsonArray();

            // 1. Add Fixed Works (from Constraints)
            for (Integer sunday : chromosome.works.get(i)) {
                sundays.add(sunday);
            }

            // 2. Add Variable Works (from Model)
            for (Integer sunday : chromosome.model.get(i)) {
                sundays.add(sunday);
            }

            root.add(storeId, sundays);
        }

        // Write to file with Pretty Printing
        try (FileWriter writer = new FileWriter(filename)) {
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            gson.toJson(root, writer);
        } catch (IOException e) {
            System.err.println("Error saving chromosome to file: " + e.getMessage());
            e.printStackTrace();
        }
    }


}
