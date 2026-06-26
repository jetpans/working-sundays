import csv
import json

from flask import request

from controllers.jobCreationController import jobCreationService
from controllers.resultStatsService import (
    DEFAULT_OPTIMIZED_RESULT,
    DEFAULT_RANDOM_RESULT,
    compute_and_cache_stats,
    ensure_default_stats_async,
    get_stats_cache,
    get_stats_status,
)
from security import api_user_required


class JobResultController:
    """
    Handles job result retrieval and presentation.
    Provides access to job outputs, solutions, and visualizations.
    """
    
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
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
                rand_name = request.args.get("random") or DEFAULT_RANDOM_RESULT
                opt_name = request.args.get("optimized") or DEFAULT_OPTIMIZED_RESULT
                job_dir = jobCreationService.resolve_job_dir(username, jobid)
                cached = get_stats_cache(job_dir, rand_name, opt_name)
                if cached is not None:
                    return {"success": True, "data": cached}, 200

                is_default_pair = (
                    rand_name == DEFAULT_RANDOM_RESULT
                    and opt_name == DEFAULT_OPTIMIZED_RESULT
                )
                if is_default_pair:
                    state = ensure_default_stats_async(job_dir)
                    if state["state"] == "ready":
                        return {"success": True, "data": state["stats"]}, 200

                    status = state.get("status") or get_stats_status(job_dir) or {}
                    if status.get("state") == "error":
                        return {"success": False, "error": status.get("error", "stats calculation failed")}, 500
                    return {
                        "success": True,
                        "status": "calculating",
                        "data": {"status": status},
                    }, 202

                stats = compute_and_cache_stats(job_dir, rand_name, opt_name)
                return {"success": True, "data": stats}, 200
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.get("/api/job/<username>/<jobid>/results/fitness-history")
        @api_user_required()
        def get_fitness_history(username: str, jobid: str):
            try:
                job_dir = jobCreationService.resolve_job_dir(username, jobid)
                history_path = job_dir / "results" / "fitness_history.csv"
                if not history_path.exists():
                    return {"success": True, "data": {"points": []}}, 200

                points = []
                with history_path.open("r", encoding="utf-8", newline="") as fh:
                    for row_number, row in enumerate(csv.DictReader(fh), 1):
                        try:
                            iteration = int(row["iteration"]) if row.get("iteration") else None
                            global_fitness = float(row["global_fitness"])
                            best_global_fitness = float(row["best_global_fitness"])
                            incoming_alpha_fitness = float(row["incoming_alpha_fitness"])
                            elapsed_ms = int(row["elapsed_ms"])
                            timestamp_ms = int(row["timestamp_ms"])
                        except (KeyError, TypeError, ValueError):
                            continue

                        points.append(
                            {
                                "step": len(points) + 1,
                                "iteration": iteration,
                                "fitness": global_fitness,
                                "global_fitness": global_fitness,
                                "best_global_fitness": best_global_fitness,
                                "incoming_alpha_fitness": incoming_alpha_fitness,
                                "elapsed_ms": elapsed_ms,
                                "timestamp_ms": timestamp_ms,
                                "line": row_number,
                            }
                        )

                return {"success": True, "data": {"points": points}}, 200
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.get("/api/job/<username>/<jobid>/result")
        @api_user_required()
        def get_job_result(username: str, jobid: str):
            try:
                job_dir = jobCreationService.resolve_job_dir(username, jobid)
                solution_path = job_dir / "results" / "solution.json"
                if not solution_path.exists():
                    return {"success": False, "error": "solution not found"}, 404

                with solution_path.open("r", encoding="utf-8") as fh:
                    payload = json.load(fh)

                return {"success": True, "data": {"solution": payload}}, 200
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404
            except Exception as e:
                return {"success": False, "error": str(e)}, 500
