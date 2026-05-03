from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid
import subprocess
import sys
import math
from typing import Any, Dict

from flask import request, jsonify

from config import AppConfig

# Ensure repo root is on sys.path for processing imports
repo_root = str(AppConfig.REPO_ROOT)
if repo_root not in sys.path:
    sys.path.append(repo_root)

try:
    from processing.calculate_radiuses import process_stores
except Exception:
    process_stores = None


@dataclass
class JobDescriptor:
    id: str
    username: str
    created_at: str
    settings: Dict[str, Any]
    value_calculator: str | None
    status: str


class JobCreationHelper:
    def __init__(self) -> None:
        self.base = AppConfig.RUNS_DIR
        self.base.mkdir(parents=True, exist_ok=True)

    def create_job(self, username: str, initial_descriptor: Dict | None = None) -> Dict:
        job_id = str(uuid.uuid4())
        job_dir = self._job_dir(username, job_id)
        job_dir.mkdir(parents=True, exist_ok=True)

        descriptor = {
            "id": job_id,
            "username": username,
            "created_at": self._utc_now(),
            "settings": {},
            "value_calculator": None,
            "status": "initialized",
        }

        if initial_descriptor:
            descriptor.update(initial_descriptor)

        self._write_json(job_dir / "descriptor.job", descriptor)

        return descriptor

    def load_stores(self, username: str, job_id: str, stores: Dict[str, Dict]) -> Dict:
        job_dir = self._ensure_job_dir(username, job_id)
        for sid, store in stores.items():
            if not all(k in store for k in ("name", "brand", "formatted_address", "coordinates")):
                raise ValueError(f"Store {sid} missing required fields")
        self._write_json(job_dir / "data.json", stores)
        return {"ok": True}

    def load_stores_with_radius(self, username: str, job_id: str, stores: Dict[str, Dict], radius_calc: str) -> Dict:
        job_dir = self._ensure_job_dir(username, job_id)
        if process_stores is None:
            raise RuntimeError("radius processing module not available")
        for sid, store in stores.items():
            if not all(k in store for k in ("name", "brand", "formatted_address", "coordinates")):
                raise ValueError(f"Store {sid} missing required fields")

        expr = (radius_calc or "").strip()
        if expr.startswith("return"):
            expr = expr[len("return"):].strip()
        if not expr:
            raise ValueError("radius_calc required")

        try:
            compiled = compile(expr, "<radius_calc>", "eval")
        except Exception as e:
            raise ValueError(f"Invalid radius_calc: {str(e)}")

        for sid, store in stores.items():
            try:
                value = eval(compiled, {"__builtins__": {}, "math": math}, {"store": store})
                store["value_for_radius"] = float(value)
            except Exception as e:
                raise ValueError(f"Error evaluating radius_calc for store {sid}: {str(e)}")

        descriptor = self._read_descriptor(job_dir)
        general_settings = descriptor.get("settings", {}).get("general", {})

        max_theoretical = general_settings.get("MAX_THEORETICAL_RADIUS_KM", 5.0)
        min_radius = general_settings.get("MIN_RADIUS_KM", 0.5)
        sensitivity = general_settings.get("COMPETITION_SENSITIVITY", 0.08)

        processed = process_stores(
            stores,
            value_key="value_for_radius",
            max_theoretical_radius_km=max_theoretical,
            min_radius_km=min_radius,
            competition_sensitivity=sensitivity,
        )
        self._write_json(job_dir / "data.json", processed)
        descriptor["value_for_radius_calculator"] = radius_calc
        self._write_json(job_dir / "descriptor.job", descriptor)

        return {"ok": True, "stores": processed}

    def load_constraints(self, username: str, job_id: str, constraints: Dict) -> Dict:
        job_dir = self._ensure_job_dir(username, job_id)
        self._write_json(job_dir / "constraints.json", constraints)
        return {"ok": True}

    def load_settings(self, username: str, job_id: str, settings: Dict) -> Dict:
        job_dir = self._ensure_job_dir(username, job_id)
        descriptor = self._read_descriptor(job_dir)
        descriptor.setdefault("settings", {})
        descriptor["settings"].update(settings)
        self._write_json(job_dir / "descriptor.job", descriptor)
        return {"ok": True}

    def load_calc(self, username: str, job_id: str, calc_string: str) -> Dict:
        job_dir = self._ensure_job_dir(username, job_id)
        descriptor = self._read_descriptor(job_dir)
        descriptor["value_calculator"] = calc_string
        self._write_json(job_dir / "descriptor.job", descriptor)
        return {"ok": True}

    def export_job(self, username: str, job_id: str) -> Dict:
        job_dir = self._ensure_job_dir(username, job_id)
        descriptor = self._read_descriptor(job_dir)

        data_path = job_dir / "data.json"
        constraints_path = job_dir / "constraints.json"
        clustering_path = job_dir / "clustering.json"

        if data_path.exists():
            descriptor["data"] = self._read_json(data_path)
        if constraints_path.exists():
            descriptor["constraints"] = self._read_json(constraints_path)
        if clustering_path.exists():
            descriptor["clustering"] = self._read_json(clustering_path)

        self._write_json(job_dir / "descriptor.job", descriptor)
        return {"ok": True, "descriptor": descriptor}

    def job_init_finish(self, username: str, job_id: str) -> Dict:
        job_dir = self._ensure_job_dir(username, job_id)
        descriptor = self._read_descriptor(job_dir)

        errors = []
        data_path = job_dir / "data.json"
        constraints_path = job_dir / "constraints.json"

        if not data_path.exists():
            errors.append("data.json missing")
        if not constraints_path.exists():
            errors.append("constraints.json missing")

        if errors:
            return {"ok": False, "errors": errors}

        stores = self._read_json(data_path)
        constraints = self._read_json(constraints_path)
        store_ids = set(stores.keys())

        # Validate constraints structure
        required_constraint_fields = {"YEAR", "SUNDAYS", "MAX_WORKS", "MAX_DOESNT_WORK"}
        missing_fields = required_constraint_fields - set(constraints.keys())
        if missing_fields:
            errors.append(f"constraints.json missing required fields: {', '.join(sorted(missing_fields))}")

        # Validate all store IDs in constraints exist in data.json
        constraint_store_ids = set()
        for key, value in constraints.items():
            if key not in required_constraint_fields:
                constraint_store_ids.add(key)
                if key not in store_ids:
                    errors.append(f"Store '{key}' in constraints.json not found in data.json")
                elif not isinstance(value, dict) or "works" not in value or "doesnt_work" not in value:
                    errors.append(f"Store '{key}' in constraints.json missing 'works' or 'doesnt_work' arrays")

        if errors:
            return {"ok": False, "errors": errors}

        calc = descriptor.get("value_calculator")

        for sid, store in stores.items():
            try:
                value = None
                if calc:
                    proc = subprocess.run([
                        AppConfig.PYTHON_BIN,
                        "-c",
                        calc,
                    ], input=json.dumps(store).encode("utf-8"), capture_output=True, check=False)

                    if proc.returncode == 0:
                        out = proc.stdout.decode().strip()
                        try:
                            value = float(out)
                        except Exception:
                            value = None
                if value is None:
                    value = float(store.get("user_ratings_total", 1))
            except Exception:
                value = 1.0

            # Store the calculated value in the store data
            store["value"] = value

            # TODO: Implement radius_km calculation using the value and radius_calculation function
            raise NotImplementedError(
                "radius_km calculation not yet implemented - awaiting radius_calculation function")

        self._write_json(data_path, stores)

        descriptor["status"] = "ready"
        self._write_json(job_dir / "descriptor.job", descriptor)

        return {"ok": True, "descriptor": descriptor}

    def get_job(self, username: str, job_id: str) -> Dict:
        job_dir = self._ensure_job_dir(username, job_id)
        descriptor = self._read_descriptor(job_dir)
        return descriptor

    def _job_dir(self, username: str, job_id: str) -> Path:
        return self.base / username / job_id

    def _ensure_job_dir(self, username: str, job_id: str) -> Path:
        job_dir = self._job_dir(username, job_id)
        if not job_dir.exists():
            raise FileNotFoundError("job not found")
        return job_dir

    def _write_json(self, path: Path, payload: Any) -> None:
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def _read_json(self, path: Path) -> Any:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _read_descriptor(self, job_dir: Path) -> Dict:
        descriptor_path = job_dir / "descriptor.job"
        if not descriptor_path.exists():
            raise FileNotFoundError("descriptor.job missing")
        return self._read_json(descriptor_path)

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()


jobCreationService = JobCreationHelper()


class JobCreationController:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        @self.app.post("/api/job/init")
        def init_job():
            body = request.get_json(silent=True) or {}
            username = body.get("username")
            if not username:
                return {"success": False, "error": "username required"}, 400
            descriptor = body.get("descriptor")
            try:
                result = jobCreationService.create_job(username, descriptor)
                return {"success": True, "data": result}, 201
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.post("/api/job/<username>/<jobid>/stores")
        def load_stores(username: str, jobid: str):
            body = request.get_json(silent=True) or {}
            stores = body.get("stores")
            if not isinstance(stores, dict):
                return {"success": False, "error": "stores must be an object mapping ids to store objects"}, 400
            try:
                jobCreationService.load_stores(username, jobid, stores)
                return {"success": True}
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404
            except ValueError as e:
                return {"success": False, "error": str(e)}, 400

        @self.app.post("/api/job/<username>/<jobid>/stores-with-radius")
        def load_stores_with_radius(username: str, jobid: str):
            body = request.get_json(silent=True) or {}
            stores = body.get("stores")
            radius_calc = body.get("radius_calc")
            if not isinstance(stores, dict):
                return {"success": False, "error": "stores must be an object mapping ids to store objects"}, 400
            if not isinstance(radius_calc, str) or not radius_calc.strip():
                return {"success": False, "error": "radius_calc must be a non-empty string"}, 400
            try:
                jobCreationService.load_stores_with_radius(username, jobid, stores, radius_calc)
                return {"success": True}
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404
            except ValueError as e:
                return {"success": False, "error": str(e)}, 400
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.post("/api/job/<username>/<jobid>/constraints")
        def load_constraints(username: str, jobid: str):
            body = request.get_json(silent=True) or {}
            constraints = body.get("constraints")
            if constraints is None:
                return {"success": False, "error": "constraints required"}, 400
            try:
                jobCreationService.load_constraints(username, jobid, constraints)
                return {"success": True}
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404

        @self.app.post("/api/job/<username>/<jobid>/settings")
        def load_settings(username: str, jobid: str):
            body = request.get_json(silent=True) or {}
            settings = body.get("settings")
            if settings is None:
                return {"success": False, "error": "settings required"}, 400
            try:
                jobCreationService.load_settings(username, jobid, settings)
                return {"success": True}
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404

        @self.app.post("/api/job/<username>/<jobid>/calc")
        def load_calc(username: str, jobid: str):
            body = request.get_json(silent=True) or {}
            calc = body.get("calc")
            if not isinstance(calc, str):
                return {"success": False, "error": "calc must be a string"}, 400
            try:
                jobCreationService.load_calc(username, jobid, calc)
                return {"success": True}
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404

        @self.app.post("/api/job/<username>/<jobid>/export")
        def export_job(username: str, jobid: str):
            try:
                result = jobCreationService.export_job(username, jobid)
                return {"success": True, "data": result.get("descriptor")}, 200
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404
            except Exception as e:
                return {"success": False, "error": str(e)}, 500

        @self.app.post("/api/job/<username>/<jobid>/finish")
        def job_init_finish(username: str, jobid: str):
            try:
                result = jobCreationService.job_init_finish(username, jobid)
                return {"success": True, "data": result}
            except FileNotFoundError:
                return {"success": False, "error": "job not found"}, 404
            except Exception as e:
                return {"success": False, "error": str(e)}, 500
