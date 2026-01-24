package project.genetic.logger;

// Log levels for the logger with integer mapping
public enum LogLevel {
    ERROR(1),
    VERBOSE(2),
    WARN(3),
    DEBUG(4);

    private final int level;

    LogLevel(int level) {
        this.level = level;
    }

    public int getLevel() {
        return level;
    }
}
