from pathlib import Path
from datetime import datetime, timezone
import json
import shutil
import subprocess
import threading
from typing import Dict, Optional

import psutil
import numpy as np
from flask import request
from flask_socketio import join_room
from flask_jwt_extended import decode_token

from config import AppConfig
from controllers.jobCreationController import jobCreationService
from controllers.resultStatsService import precompute_default_stats
from security import api_user_required
import os

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
        # Define helper function at method scope
        def _square_corners_latlon(lat, lon, half_side_m):
            from math import radians, degrees, sin, cos
            R = 6371000.0
            dlat = half_side_m / R
            dlon = half_side_m / (R * cos(radians(lat)))
            north = lat + degrees(dlat)
            south = lat - degrees(dlat)
            east = lon + degrees(dlon)
            west = lon - degrees(dlon)
            return [[south, west], [south, east], [north, east], [north, west], [south, west]]

        @self.app.get("/api/jobs/<username>")
        @api_user_required()
        def get_jobs(username: str):
            try:
                job_ids = jobCreationService.list_job_ids(username)
                return {"success": True, "data": job_ids}, 200
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.get("/api/job/<username>/<jobid>")
        @api_user_required()
        def get_job_info(username: str, jobid: str):
            try:
                descriptor = jobCreationService.get_job(username, jobid)
                job_dir = jobCreationService.resolve_job_dir(username, jobid)

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
                        "started_at": run_info.get("started_at"),
                        "finished_at": run_info.get("finished_at"),
                        "duration_seconds": run_info.get("duration_seconds"),
                        "java_started_at": run_info.get("java_started_at"),
                        "java_finished_at": run_info.get("java_finished_at"),
                        "java_duration_seconds": run_info.get("java_duration_seconds"),
                    }
                }

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
                    job_info["data"] = None
                    job_info["constraints"] = None
                
                return {"success": True, "data": job_info}, 200
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.get("/api/job/<username>/<jobid>/run-info")
        @api_user_required()
        def get_run_info(username: str, jobid: str):
            try:
                descriptor = jobCreationService.get_job(username, jobid)
                run_info = descriptor.get("run_info") or {}
                return {
                    "success": True,
                    "data": {
                        "status": run_info.get("status", "Uninitialized"),
                        "created_at": descriptor.get("created_at"),
                        "updated_at": run_info.get("updated_at"),
                        "started_at": run_info.get("started_at"),
                        "finished_at": run_info.get("finished_at"),
                        "duration_seconds": run_info.get("duration_seconds"),
                        "java_started_at": run_info.get("java_started_at"),
                        "java_finished_at": run_info.get("java_finished_at"),
                        "java_duration_seconds": run_info.get("java_duration_seconds"),
                    },
                }, 200
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.post("/api/job/<username>/<jobid>/run")
        @api_user_required()
        def run_job(username: str, jobid: str):
            key = f"{username}:{jobid}"
            if key in self._runs and self._runs[key].get("process") is not None:
                return {"success": False, "error": "job already running"}, 409

            job_dir = jobCreationService.resolve_job_dir(username, jobid)
            if not job_dir.exists():
                return {"success": False, "error": "job not found"}, 404

            if not AppConfig.JAVA_JAR:
                return {"success": False, "error": "JAVA_JAR not configured"}, 500

            results_dir = job_dir / "results"
            if results_dir.exists():
                try:
                    shutil.rmtree(results_dir)
                except PermissionError:
                    # Handle permission errors when deleting results (e.g., file locked or wrong permissions)
                    import stat

                    def handle_remove_readonly(func, path, exc):
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    shutil.rmtree(results_dir, onerror=handle_remove_readonly)
            results_dir.mkdir(parents=True, exist_ok=True)

            run_log_path = job_dir / "run.log"
            try:
                run_log_path.write_text("")
            except Exception:
                pass

            descriptor_path = job_dir / "descriptor.job"
            try:
                descriptor = jobCreationService._read_descriptor(job_dir)
                started_at = self._utc_now()
                descriptor["run_info"] = {
                    "status": "Running",
                    "updated_at": started_at,
                    "started_at": started_at,
                    "finished_at": None,
                    "duration_seconds": None,
                    "java_started_at": None,
                    "java_finished_at": None,
                    "java_duration_seconds": None,
                }
                jobCreationService._write_json(descriptor_path, descriptor)
                self._emit_run_status(key, descriptor["run_info"]["status"], descriptor["run_info"]["updated_at"])
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

            instance_folder = str(job_dir)
            command = [
                AppConfig.JAVA_BIN,
                "-jar",
                AppConfig.JAVA_JAR,
                instance_folder,
                "--export-random",
            ]

            def run_worker():
                proc: Optional[subprocess.Popen[str]] = None
                try:
                    java_started_at = self._utc_now()
                    self._update_run_status(
                        job_dir,
                        "Running",
                        {
                            "java_started_at": java_started_at,
                            "java_finished_at": None,
                            "java_duration_seconds": None,
                        },
                    )
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
                        with run_log_path.open("a", encoding="utf-8") as rl:
                            for line in proc.stdout:
                                if line is None:
                                    continue
                                text = line.rstrip("\n")
                                try:
                                    rl.write(text + "\n")
                                    rl.flush()
                                except Exception:
                                    pass
                                self.socketio.emit(
                                    "run_log",
                                    text,
                                    room=key,
                                )

                    exit_code = proc.wait()
                    java_finished_at = self._utc_now()
                    self._update_run_status(
                        job_dir,
                        "Calculating stats" if exit_code == 0 else "Error",
                        {
                            "java_finished_at": java_finished_at,
                            "java_duration_seconds": self._duration_seconds(java_started_at, java_finished_at),
                        },
                    )
                    if exit_code == 0:
                        self._emit_run_status(key, "Calculating stats", self._utc_now())
                        try:
                            precompute_default_stats(job_dir)
                        except Exception as e:
                            try:
                                with run_log_path.open("a", encoding="utf-8") as rl:
                                    rl.write(f"\n--- STATS PRECOMPUTE FAILED: {e} ---\n")
                            except Exception:
                                pass
                        status = "Complete"
                    else:
                        status = "Error"

                    finished_at = self._utc_now()
                    self._update_run_status(
                        job_dir,
                        status,
                        {
                            "finished_at": finished_at,
                            "duration_seconds": self._run_duration_seconds(job_dir, finished_at),
                        },
                    )
                    self._emit_run_status(key, status, self._utc_now())
                except Exception:
                    finished_at = self._utc_now()
                    self._update_run_status(
                        job_dir,
                        "Error",
                        {
                            "finished_at": finished_at,
                            "duration_seconds": self._run_duration_seconds(job_dir, finished_at),
                        },
                    )
                    self._emit_run_status(key, "Error", self._utc_now())
                finally:
                    if key in self._runs:
                        self._runs.pop(key, None)

            thread = threading.Thread(target=run_worker, daemon=True)
            thread.start()

            return {"success": True, "data": {"status": "Running"}}, 202

        @self.app.post("/api/job/<username>/<jobid>/terminate")
        @api_user_required()
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

            job_dir = jobCreationService.resolve_job_dir(username, jobid)
            finished_at = self._utc_now()
            self._update_run_status(
                job_dir,
                "Error",
                {
                    "finished_at": finished_at,
                    "duration_seconds": self._run_duration_seconds(job_dir, finished_at),
                },
            )
            self._emit_run_status(key, "Error", self._utc_now())

            try:
                (job_dir / "run.log").write_text((job_dir / "run.log").read_text() + "\n--- TERMINATED ---\n")
            except Exception:
                pass
            self._runs.pop(key, None)

            return {"success": True}, 200

        @self.app.delete("/api/job/<username>/<jobid>")
        @api_user_required()
        def delete_job(username: str, jobid: str):
            try:
                job_dir = jobCreationService.resolve_job_dir(username, jobid)
                if not job_dir.exists():
                    return {"success": False, "error": "job not found"}, 404

                shutil.rmtree(job_dir)
                return {"success": True}, 200
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.get("/api/job/<username>/<jobid>/runlog")
        @api_user_required()
        def get_run_log(username: str, jobid: str):
            try:
                job_dir = jobCreationService.resolve_job_dir(username, jobid)
                run_log = job_dir / "run.log"
                if not run_log.exists():
                    return {"success": True, "data": {"lines": [], "updated_at": None}}, 200
                text = run_log.read_text(encoding="utf-8")
                lines = [l for l in text.splitlines()]
                updated_at = None
                try:
                    updated_at = run_log.stat().st_mtime
                except Exception:
                    updated_at = None
                return {"success": True, "data": {"lines": lines, "updated_at": updated_at}}, 200
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.get("/api/job/<username>/<jobid>/runlog/tail")
        @api_user_required()
        def get_run_log_tail(username: str, jobid: str):
            try:
                offset = int(request.args.get("offset", 0))
                max_bytes = int(request.args.get("max_bytes", 65536))
                job_dir = jobCreationService.resolve_job_dir(username, jobid)
                run_log = job_dir / "run.log"
                if not run_log.exists():
                    return {"success": True, "data": {"lines": [], "offset": 0, "eof": True}}, 200

                file_size = run_log.stat().st_size
                if offset < 0:
                    offset = 0
                if offset > file_size:
                    offset = file_size

                new_offset = offset
                lines = []
                with run_log.open("rb") as fh:
                    fh.seek(offset)
                    data = fh.read(max_bytes)
                    if not data:
                        return {"success": True, "data": {"lines": [], "offset": file_size, "eof": offset >= file_size}}, 200
                    try:
                        text = data.decode("utf-8")
                    except Exception:
                        text = data.decode("utf-8", errors="ignore")

                    if not text.endswith("\n"):
                        extra = fh.readline()
                        try:
                            extra_text = extra.decode("utf-8")
                        except Exception:
                            extra_text = extra.decode("utf-8", errors="ignore")
                        text += extra_text

                    new_offset = fh.tell()

                lines = [l for l in text.splitlines()]
                eof = new_offset >= file_size
                return {"success": True, "data": {"lines": lines, "offset": new_offset, "eof": eof}}, 200
            except Exception as e:
                return {"success": False, "error": str(e)}, 500


    def register_socket_events(self):
        @self.socketio.on("run_subscribe")
        def handle_run_subscribe(payload):
            token = payload.get("token")
            username = payload.get("username")
            jobid = payload.get("jobId")
            if not token or not username or not jobid:
                return
            try:
                decoded = decode_token(token)
            except Exception:
                return

            if decoded.get("role") != "user":
                return
            if decoded.get("sub") != username:
                return

            key = f"{username}:{jobid}"
            join_room(key)
            try:
                descriptor = jobCreationService.get_job(username, jobid)
                run_info = descriptor.get("run_info") or {}
                self.socketio.emit(
                    "run_status",
                    {
                        "status": run_info.get("status", "Uninitialized"),
                        "updated_at": run_info.get("updated_at"),
                    },
                    room=key,
                )
            except Exception:
                pass

    def _update_run_status(self, job_dir: Path, status: str, updates: dict | None = None) -> None:
        try:
            descriptor = jobCreationService._read_descriptor(job_dir)
            run_info = descriptor.get("run_info") or {}
            run_info["status"] = status
            run_info["updated_at"] = self._utc_now()
            if updates:
                run_info.update(updates)
            descriptor["run_info"] = run_info
            jobCreationService._write_json(job_dir / "descriptor.job", descriptor)
        except Exception:
            pass

    def _run_duration_seconds(self, job_dir: Path, finished_at: str) -> float | None:
        try:
            descriptor = jobCreationService._read_descriptor(job_dir)
            started_at = (descriptor.get("run_info") or {}).get("started_at")
            return self._duration_seconds(started_at, finished_at)
        except Exception:
            return None

    @staticmethod
    def _duration_seconds(started_at: str | None, finished_at: str | None) -> float | None:
        if not started_at or not finished_at:
            return None
        try:
            start = datetime.fromisoformat(started_at)
            finish = datetime.fromisoformat(finished_at)
            return max(0.0, (finish - start).total_seconds())
        except Exception:
            return None

    def _emit_run_status(self, room: str, status: str, updated_at: str) -> None:
        try:
            self.socketio.emit(
                "run_status",
                {
                    "status": status,
                    "updated_at": updated_at,
                },
                room=room,
            )
        except Exception:
            pass

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

