from flask import request
from security import api_user_required


class JobResultController:
    """
    Handles job result retrieval and presentation.
    Provides access to job outputs, solutions, metrics, and visualizations.
    """
    
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        @self.app.get("/api/job/<username>/<jobid>/result")
        @api_user_required()
        def get_job_result(username: str, jobid: str):
            raise NotImplementedError("Job result retrieval not yet implemented")

        @self.app.get("/api/job/<username>/<jobid>/metrics")
        @api_user_required()
        def get_job_metrics(username: str, jobid: str):
            raise NotImplementedError("Job metrics retrieval not yet implemented")

        @self.app.get("/api/job/<username>/<jobid>/visualization")
        @api_user_required()
        def get_job_visualization(username: str, jobid: str):
            raise NotImplementedError("Job visualization not yet implemented")

        @self.app.get("/api/job/<username>/<jobid>/logs")
        @api_user_required()
        def get_job_logs(username: str, jobid: str):
            raise NotImplementedError("Job logs retrieval not yet implemented")
