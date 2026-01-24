package project.genetic.logger;

import java.io.OutputStream;

public abstract class Logger {

    private OutputStream out;
    protected boolean on = true;
    protected LogLevel logLevel = LogLevel.DEBUG;

    public Logger(OutputStream out) {
        this.out = out;
    }

    public void println(LogLevel level, String message) {
        if (level.getLevel() > logLevel.getLevel()) return;
        if (!on) return;
        try {
            out.write((message + "\n").getBytes());
            out.flush();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void printf(LogLevel level, String format, Object... args) {
        if (level.getLevel() > logLevel.getLevel()) return;
        if (!on) return;
        try {
            out.write((String.format(format, args)).getBytes());
            out.flush();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
