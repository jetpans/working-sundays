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
from security import api_user_required


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
                shutil.rmtree(results_dir)
            results_dir.mkdir(parents=True, exist_ok=True)

            run_log_path = job_dir / "run.log"
            try:
                run_log_path.write_text("")
            except Exception:
                pass

            descriptor_path = job_dir / "descriptor.job"
            try:
                descriptor = jobCreationService._read_descriptor(job_dir)
                descriptor["run_info"] = {
                    "status": "Running",
                    "updated_at": self._utc_now(),
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
                    status = "Complete" if exit_code == 0 else "Error"
                    self._update_run_status(job_dir, status)
                    self._emit_run_status(key, status, self._utc_now())
                except Exception:
                    self._update_run_status(job_dir, "Error")
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
            self._update_run_status(job_dir, "Error")
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

        @self.app.get("/api/job/<username>/<jobid>/results")
        @api_user_required()
        def list_results(username: str, jobid: str):
            try:
                job_dir = jobCreationService.resolve_job_dir(username, jobid)
                results_dir = job_dir / "results"
                if not results_dir.exists():
                    return {"success": True, "data": []}, 200
                files = [p.name for p in results_dir.iterdir() if p.is_file()]
                return {"success": True, "data": sorted(files)}, 200
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.get("/api/job/<username>/<jobid>/results/file")
        @api_user_required()
        def get_result_file(username: str, jobid: str):
            try:
                name = request.args.get("name")
                if not name:
                    return {"success": False, "error": "missing name"}, 400
                job_dir = jobCreationService.resolve_job_dir(username, jobid)
                file_path = job_dir / "results" / name
                if not file_path.exists():
                    return {"success": False, "error": "file not found"}, 404
                text = file_path.read_text(encoding="utf-8")
                data = json.loads(text)
                return {"success": True, "data": data}, 200
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.get("/api/job/<username>/<jobid>/results/polygons")
        @api_user_required()
        def get_result_polygons(username: str, jobid: str):
            try:
                name = request.args.get("name")
                if not name:
                    return {"success": False, "error": "missing name"}, 400
                job_dir = jobCreationService.resolve_job_dir(username, jobid)
                data_path = job_dir / "data.json"
                if not data_path.exists():
                    return {"success": False, "error": "data.json not found"}, 404
                data = jobCreationService._read_json(data_path)

                file_path = job_dir / "results" / name
                if not file_path.exists():
                    return {"success": False, "error": "solution file not found"}, 404
                solution = jobCreationService._read_json(file_path)

                constraints_path = job_dir / "constraints.json"
                total_sundays = None
                if constraints_path.exists():
                    try:
                        constraints = jobCreationService._read_json(constraints_path)
                        total_sundays = constraints.get("SUNDAYS")
                    except Exception:
                        total_sundays = None

                sundays_polygons = []
                for sunday in range(total_sundays if total_sundays is not None else 0):
                    entries = []
                    for store_id, sundays_list in solution.items():
                        try:
                            if sunday not in sundays_list:
                                continue
                        except Exception:
                            continue

                        store_info = data.get(store_id)
                        if not store_info:
                            continue
                        coords = store_info.get("coordinates", [0, 0])
                        lon, lat = coords[0], coords[1]
                        radius_km = store_info.get("radius_km", 0)
                        half_side_m = (radius_km * 1000) / 2.0
                        poly = _square_corners_latlon(lat, lon, half_side_m)
                        entries.append({
                            "store_id": store_id,
                            "coords": poly,
                        })
                    sundays_polygons.append({"sunday": sunday, "polygons": entries})

                return {"success": True, "data": {"sundays": sundays_polygons}}, 200
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.get("/api/job/<username>/<jobid>/results/stats")
        @api_user_required()
        def get_results_stats(username: str, jobid: str):
            try:
                rand_name = request.args.get("random") or "random_start.json"
                opt_name = request.args.get("optimized") or "solution.json"
                job_dir = jobCreationService.resolve_job_dir(username, jobid)
                results_dir = job_dir / "results"
                rand_path = results_dir / rand_name
                opt_path = results_dir / opt_name

                data_path = job_dir / "data.json"
                constraints_path = job_dir / "constraints.json"
                if not data_path.exists() or not constraints_path.exists():
                    return {"success": False, "error": "data or constraints missing"}, 400
                data = jobCreationService._read_json(data_path)
                constraints = jobCreationService._read_json(constraints_path)
                total_sundays = constraints.get("SUNDAYS", 0)

                cache_file = results_dir / "_stats_cache.json"
                rand_mtime = rand_path.stat().st_mtime if rand_path.exists() else None
                opt_mtime = opt_path.stat().st_mtime if opt_path.exists() else None

                if cache_file.exists():
                    try:
                        cache = jobCreationService._read_json(cache_file)
                        if cache.get("rand_mtime") == rand_mtime and cache.get("opt_mtime") == opt_mtime:
                            return {"success": True, "data": cache.get("stats")}, 200
                    except Exception:
                        pass

                from util import fast_create_boxes, fast_union_intersect

                def compute_fitness_for_solution(sol_path):
                    if not sol_path.exists():
                        return [0.0 for _ in range(total_sundays)], 0.0
                    sol = jobCreationService._read_json(sol_path)
                    per_sunday = []
                    store_ids = list(sol.keys())
                    coords = [data[sid]["coordinates"] for sid in store_ids]
                    for sunday in range(total_sundays):
                        radii = []
                        for sid in store_ids:
                            try:
                                radii.append(data[sid]["radius_km"] if sunday in sol.get(sid, []) else 0.0)
                            except Exception:
                                radii.append(0.0)
                        try:
                            boxes = fast_create_boxes([c for c in coords], np.array(radii))
                            union, intersect = fast_union_intersect(boxes)
                            per_sunday.append(union - intersect)
                        except Exception:
                            per_sunday.append(0.0)
                    overall = sum(per_sunday) / max(1, len(per_sunday))
                    return per_sunday, overall

                rand_per, rand_overall = compute_fitness_for_solution(rand_path)
                opt_per, opt_overall = compute_fitness_for_solution(opt_path)

                delta_per = [o - r for o, r in zip(opt_per, rand_per)]

                stats = {}
                stats["overall"] = {"random": rand_overall,
                                    "optimized": opt_overall, "delta": opt_overall - rand_overall}
                stats["per_sunday"] = [{"sunday": i, "random": rand_per[i],
                                        "optimized": opt_per[i], "delta": delta_per[i]} for i in range(len(delta_per))]

                arr = np.array(delta_per)
                stats["delta_summary"] = {
                    "sum": float(np.sum(arr)),
                    "mean": float(np.mean(arr)),
                    "median": float(np.median(arr)),
                    "min": float(np.min(arr)),
                    "max": float(np.max(arr)),
                }

                pct = []
                for r, o in zip(rand_per, opt_per):
                    if r == 0:
                        pct.append(None)
                    else:
                        pct.append((o - r) / abs(r) * 100.0)
                stats["per_sunday_pct"] = pct

                try:
                    jobCreationService._write_json(
                        cache_file, {"rand_mtime": rand_mtime, "opt_mtime": opt_mtime, "stats": stats})
                except Exception:
                    pass

                return {"success": True, "data": stats}, 200
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

