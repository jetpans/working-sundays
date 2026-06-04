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
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", str(REPO_ROOT))).resolve()
    RUNS_DIR = Path(os.getenv("RUNS_DIR", str(APP_DIR / "jobs"))).resolve()
    AUTH_DIR = Path(os.getenv("AUTH_DIR", str(APP_DIR / "auth"))).resolve()
    AUTH_USERS_FILE = Path(os.getenv("AUTH_USERS_FILE", str(AUTH_DIR / "users.json"))).resolve()
    AUTH_JWT_SECRET_FILE = Path(
        os.getenv("AUTH_JWT_SECRET_FILE", str(AUTH_DIR / ".jwt_secret"))
    ).resolve()

    JAVA_BIN = os.getenv("JAVA_BIN", "java")
    JAVA_JAR = os.getenv("JAVA_JAR", "")
    PYTHON_BIN = os.getenv("PYTHON_BIN", "python")
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "12"))

    METRICS_SAMPLE_SECONDS = float(os.getenv("METRICS_SAMPLE_SECONDS", "1.0"))
