from datetime import datetime, timezone

from security import api_user_required


class HealthController:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        @self.app.get("/api/heartbeat")
        @api_user_required(match_username=False)
        def heartbeat():
            return {
                "success": True,
                "data": {
                    "status": "ok",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
