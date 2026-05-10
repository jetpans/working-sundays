from config import AppConfig

from app import app, socketio

if __name__ == "__main__":
    socketio.run(app, host=AppConfig.HOST, port=AppConfig.PORT, debug=AppConfig.DEBUG)
