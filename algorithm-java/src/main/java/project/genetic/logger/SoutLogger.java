package project.genetic.logger;

public class SoutLogger extends Logger {

    public SoutLogger() {
        super(System.out);
    }

    public SoutLogger(LogLevel level) {
        super(System.out);
        super.logLevel = level;
    }
}
