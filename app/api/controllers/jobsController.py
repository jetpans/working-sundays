from pathlib import Path
from datetime import datetime, timezone
import json
import shutil
import subprocess
import threading
from typing import Dict, Optional

import psutil
from flask import request
from flask_socketio import join_room

from config import AppConfig
from controllers.jobCreationController import jobCreationService


class JobsController:
    """
    Handles post-creation job operations:
    - List all jobs for a user
    - Get comprehensive job information
    - Run a job
    """
    
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self._runs: Dict[str, Dict] = {}
        self.register_routes()
        self.register_socket_events()

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
                run_info = descriptor.get("run_info") or {}

                job_info = {
                    "descriptor": descriptor,
                    "files": {
                        "has_data": (job_dir / "data.json").exists(),
                        "has_constraints": (job_dir / "constraints.json").exists(),
                        "has_settings": descriptor.get("settings") is not None,
                        "has_value_calculator": descriptor.get("value_calculator") is not None,
                    },
                    "run_info": {
                        "status": run_info.get("status", "Uninitialized"),
                        "created_at": descriptor.get("created_at"),
                        "updated_at": run_info.get("updated_at"),
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
            Starts a background process and streams logs over websocket.
            """
            key = f"{username}:{jobid}"
            if key in self._runs and self._runs[key].get("process") is not None:
                return {"success": False, "error": "job already running"}, 409

            job_dir = AppConfig.RUNS_DIR / username / jobid
            if not job_dir.exists():
                return {"success": False, "error": "job not found"}, 404

            if not AppConfig.JAVA_JAR:
                return {"success": False, "error": "JAVA_JAR not configured"}, 500

            results_dir = job_dir / "results"
            if results_dir.exists():
                shutil.rmtree(results_dir)
            results_dir.mkdir(parents=True, exist_ok=True)

            descriptor_path = job_dir / "descriptor.job"
            try:
                descriptor = jobCreationService._read_descriptor(job_dir)
                descriptor["run_info"] = {
                    "status": "Running",
                    "updated_at": self._utc_now(),
                }
                jobCreationService._write_json(descriptor_path, descriptor)
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

            instance_folder = str(job_dir)
            command = [AppConfig.JAVA_BIN, "-jar", AppConfig.JAVA_JAR, instance_folder]

            def run_worker():
                proc: Optional[subprocess.Popen[str]] = None
                try:
                    proc = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                    )
                    self._runs[key] = {
                        "process": proc,
                        "thread": threading.current_thread(),
                    }

                    if proc.stdout:
                        for line in proc.stdout:
                            if line is None:
                                continue
                            self.socketio.emit(
                                "run_log",
                                line.rstrip("\n"),
                                room=key,
                            )

                    exit_code = proc.wait()
                    status = "Complete" if exit_code == 0 else "Error"
                    self._update_run_status(job_dir, status)
                except Exception:
                    self._update_run_status(job_dir, "Error")
                finally:
                    if key in self._runs:
                        self._runs.pop(key, None)

            thread = threading.Thread(target=run_worker, daemon=True)
            thread.start()

            return {"success": True, "data": {"status": "Running"}}, 202

        @self.app.post("/api/job/<username>/<jobid>/terminate")
        def terminate_job(username: str, jobid: str):
            key = f"{username}:{jobid}"
            run_entry = self._runs.get(key)
            if not run_entry or not run_entry.get("process"):
                return {"success": False, "error": "job not running"}, 409

            proc = run_entry["process"]
            try:
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                parent.kill()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

            job_dir = AppConfig.RUNS_DIR / username / jobid
            self._update_run_status(job_dir, "Error")

            self._runs.pop(key, None)

            return {"success": True}, 200

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

    def register_socket_events(self):
        @self.socketio.on("run_subscribe")
        def handle_run_subscribe(payload):
            username = payload.get("username")
            jobid = payload.get("jobId")
            if not username or not jobid:
                return
            key = f"{username}:{jobid}"
            join_room(key)

    def _update_run_status(self, job_dir: Path, status: str) -> None:
        try:
            descriptor = jobCreationService._read_descriptor(job_dir)
            descriptor["run_info"] = {
                "status": status,
                "updated_at": self._utc_now(),
            }
            jobCreationService._write_json(job_dir / "descriptor.job", descriptor)
        except Exception:
            pass

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()
