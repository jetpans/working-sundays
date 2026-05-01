from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    APP_DIR = Path(__file__).resolve().parent
    REPO_ROOT = Path(__file__).resolve().parents[2]

    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", str(REPO_ROOT))).resolve()
    RUNS_DIR = Path(os.getenv("RUNS_DIR", str(APP_DIR / "runs"))).resolve()

    JAVA_BIN = os.getenv("JAVA_BIN", "java")
    JAVA_JAR = os.getenv("JAVA_JAR", "")
    PYTHON_BIN = os.getenv("PYTHON_BIN", "python")

    METRICS_SAMPLE_SECONDS = float(os.getenv("METRICS_SAMPLE_SECONDS", "1.0"))
