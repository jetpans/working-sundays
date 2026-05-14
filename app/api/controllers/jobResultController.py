import json

import numpy as np
from flask import request

from controllers.jobCreationController import jobCreationService
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
