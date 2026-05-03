from pathlib import Path
import json
import shutil
from flask import request

from config import AppConfig
from controllers.jobCreationController import jobCreationService


class JobsController:
    """
    Handles post-creation job operations:
    - List all jobs for a user
    - Get comprehensive job information
    - Run a job
    """
    
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        @self.app.get("/api/jobs/<username>")
        def get_jobs(username: str):
            """
            Get all job IDs for a given username.
            Returns: {"success": True, "data": [job_id1, job_id2, ...]}
            """
            try:
                user_dir = AppConfig.RUNS_DIR / username
                if not user_dir.exists():
                    return {"success": True, "data": []}, 200
                
                job_ids = [d.name for d in user_dir.iterdir() if d.is_dir()]
                return {"success": True, "data": sorted(job_ids)}, 200
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.get("/api/job/<username>/<jobid>")
        def get_job_info(username: str, jobid: str):
            """
            Get comprehensive job information including descriptor, status, and file availability.
            Returns all relevant data for frontend display.
            """
            try:
                descriptor = jobCreationService.get_job(username, jobid)
                job_dir = AppConfig.RUNS_DIR / username / jobid
                
                # Build comprehensive job info
                job_info = {
                    "descriptor": descriptor,
                    "files": {
                        "has_data": (job_dir / "data.json").exists(),
                        "has_constraints": (job_dir / "constraints.json").exists(),
                        "has_settings": descriptor.get("settings") is not None,
                        "has_value_calculator": descriptor.get("value_calculator") is not None,
                    },
                    "run_info": {
                        "status": descriptor.get("status", "unknown"),
                        "created_at": descriptor.get("created_at"),
                    }
                }

                # If files exist, include their content so frontend can preload edit forms
                data_path = job_dir / "data.json"
                constraints_path = job_dir / "constraints.json"
                try:
                    if data_path.exists():
                        job_info["data"] = jobCreationService._read_json(data_path)
                    else:
                        job_info["data"] = None

                    if constraints_path.exists():
                        job_info["constraints"] = jobCreationService._read_json(constraints_path)
                    else:
                        job_info["constraints"] = None
                except Exception:
                    # If reading files fails, return their existence flags but omit content
                    job_info["data"] = None
                    job_info["constraints"] = None
                
                return {"success": True, "data": job_info}, 200
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.post("/api/job/<username>/<jobid>/run")
        def run_job(username: str, jobid: str):
            """
            Run the job using the Java algorithm with appropriate settings.
            Placeholder for actual job execution logic.
            """
            raise NotImplementedError("Job execution not yet implemented - awaiting Java integration")

        @self.app.delete("/api/job/<username>/<jobid>")
        def delete_job(username: str, jobid: str):
            """
            Delete a job directory for a given username and job ID.
            """
            try:
                job_dir = AppConfig.RUNS_DIR / username / jobid
                if not job_dir.exists():
                    return {"success": False, "error": "job not found"}, 404

                shutil.rmtree(job_dir)
                return {"success": True}, 200
            except Exception as e:
                return {"success": False, "error": str(e)}, 500
