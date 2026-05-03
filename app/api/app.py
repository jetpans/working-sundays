import os

from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

from config import AppConfig
from controllers.healthController import HealthController
from controllers.jobCreationController import JobCreationController
from controllers.jobsController import JobsController
from controllers.jobResultController import JobResultController

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

socketio = SocketIO(app, cors_allowed_origins=allowed_origins)


@app.route("/")
def home():
    return {"success": True, "data": "API is running"}


healthController = HealthController(app)
jobCreationController = JobCreationController(app)
jobsController = JobsController(app, socketio)
jobResultController = JobResultController(app)


if __name__ == "__main__":
    socketio.run(app, host=AppConfig.HOST, port=AppConfig.PORT, debug=AppConfig.DEBUG)
