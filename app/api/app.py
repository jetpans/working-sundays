import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS

from config import AppConfig
from controllers.authController import AuthController
from controllers.healthController import HealthController
from controllers.jobCreationController import JobCreationController
from controllers.jobsController import JobsController
from controllers.jobResultController import JobResultController
from security import ensure_jwt_secret
from docs import setup_swagger

load_dotenv()

app = Flask(__name__)

env = os.environ.get("FLASK_ENV", AppConfig.FLASK_ENV)

if env == "production":
    allowed_origins = [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
    if not allowed_origins:
        allowed_origins = ["*"]
else:
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

bcrypt = Bcrypt(app)
app.config["JWT_SECRET_KEY"] = ensure_jwt_secret()
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=AppConfig.JWT_ACCESS_TOKEN_EXPIRES_HOURS)
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"

jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins=allowed_origins, async_mode="gevent")

# Setup Swagger documentation
setup_swagger(app)

AppConfig.RUNS_DIR.mkdir(parents=True, exist_ok=True)


@app.route("/")
def home():
    return {"success": True, "data": "API is running"}


healthController = HealthController(app)
authController = AuthController(app, bcrypt)
jobCreationController = JobCreationController(app)
jobsController = JobsController(app, socketio)
jobResultController = JobResultController(app)


if __name__ == "__main__":
    socketio.run(app, host=AppConfig.HOST, port=AppConfig.PORT, debug=AppConfig.DEBUG)
