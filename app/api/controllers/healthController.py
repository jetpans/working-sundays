from datetime import datetime, timezone


class HealthController:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        @self.app.get("/api/heartbeat")
        def heartbeat():
            return {
                "success": True,
                "data": {
                    "status": "ok",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
