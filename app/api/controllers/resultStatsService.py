from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import threading
from typing import Any

import numpy as np

from controllers.jobCreationController import jobCreationService


DEFAULT_RANDOM_RESULT = "random_start.json"
DEFAULT_OPTIMIZED_RESULT = "solution.json"
STATS_CACHE_FILE = "_stats_cache.json"
STATS_STATUS_FILE = "_stats_status.json"

_stats_lock = threading.Lock()
_stats_threads: dict[str, threading.Thread] = {}


class StatsComputationError(Exception):
    pass


def get_stats_cache(job_dir: Path, random_name: str, optimized_name: str) -> dict[str, Any] | None:
    results_dir = job_dir / "results"
    cache_file = results_dir / STATS_CACHE_FILE
    rand_path = results_dir / random_name
    opt_path = results_dir / optimized_name

    if not cache_file.exists():
        return None

    try:
        cache = jobCreationService._read_json(cache_file)
    except Exception:
        return None

    if (
        cache.get("random_name") == random_name
        and cache.get("optimized_name") == optimized_name
        and cache.get("rand_mtime") == _mtime(rand_path)
        and cache.get("opt_mtime") == _mtime(opt_path)
    ):
        return cache.get("stats")

    return None


def get_stats_status(job_dir: Path) -> dict[str, Any] | None:
    status_file = job_dir / "results" / STATS_STATUS_FILE
    if not status_file.exists():
        return None

    try:
        return jobCreationService._read_json(status_file)
    except Exception:
        return None


def ensure_default_stats_async(job_dir: Path) -> dict[str, Any]:
    cached = get_stats_cache(job_dir, DEFAULT_RANDOM_RESULT, DEFAULT_OPTIMIZED_RESULT)
    if cached is not None:
        return {"state": "ready", "stats": cached}

    status = get_stats_status(job_dir)
    if status and status.get("state") == "calculating":
        return {"state": "calculating", "status": status}
    if status and status.get("state") == "error":
        return {"state": "error", "status": status}

    _start_default_stats_thread(job_dir)
    status = get_stats_status(job_dir)
    return {"state": "calculating", "status": status}


def precompute_default_stats(job_dir: Path) -> dict[str, Any]:
    return compute_and_cache_stats(job_dir, DEFAULT_RANDOM_RESULT, DEFAULT_OPTIMIZED_RESULT)


def compute_and_cache_stats(
    job_dir: Path,
    random_name: str,
    optimized_name: str,
) -> dict[str, Any]:
    results_dir = job_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    rand_path = results_dir / random_name
    opt_path = results_dir / optimized_name
    data_path = job_dir / "data.json"
    constraints_path = job_dir / "constraints.json"

    _write_status(results_dir, "calculating", random_name, optimized_name)

    try:
        if not data_path.exists() or not constraints_path.exists():
            raise StatsComputationError("data or constraints missing")
        if not rand_path.exists():
            raise StatsComputationError(f"{random_name} missing")
        if not opt_path.exists():
            raise StatsComputationError(f"{optimized_name} missing")

        data = jobCreationService._read_json(data_path)
        constraints = jobCreationService._read_json(constraints_path)
        total_sundays = int(constraints.get("SUNDAYS", 0) or 0)

        rand_per, rand_overall = _compute_fitness_for_solution(rand_path, data, total_sundays)
        opt_per, opt_overall = _compute_fitness_for_solution(opt_path, data, total_sundays)
        delta_per = [o - r for o, r in zip(opt_per, rand_per)]

        stats = _build_stats(rand_per, rand_overall, opt_per, opt_overall, delta_per)
        jobCreationService._write_json(
            results_dir / STATS_CACHE_FILE,
            {
                "random_name": random_name,
                "optimized_name": optimized_name,
                "rand_mtime": _mtime(rand_path),
                "opt_mtime": _mtime(opt_path),
                "created_at": _utc_now(),
                "stats": stats,
            },
        )
        _write_status(results_dir, "ready", random_name, optimized_name)
        return stats
    except Exception as exc:
        _write_status(results_dir, "error", random_name, optimized_name, str(exc))
        raise


def _start_default_stats_thread(job_dir: Path) -> None:
    key = str(job_dir.resolve())
    with _stats_lock:
        existing = _stats_threads.get(key)
        if existing and existing.is_alive():
            return

        thread = threading.Thread(
            target=_run_default_stats_thread,
            args=(job_dir, key),
            daemon=True,
        )
        _stats_threads[key] = thread
        thread.start()


def _run_default_stats_thread(job_dir: Path, key: str) -> None:
    try:
        precompute_default_stats(job_dir)
    except Exception:
        pass
    finally:
        with _stats_lock:
            _stats_threads.pop(key, None)


def _compute_fitness_for_solution(
    sol_path: Path,
    data: dict[str, Any],
    total_sundays: int,
) -> tuple[list[float], float]:
    from util import fast_create_boxes, fast_union_intersect

    sol = jobCreationService._read_json(sol_path)
    per_sunday = []
    store_ids = [sid for sid in sol.keys() if sid in data]

    for sunday in range(total_sundays):
        active_coords = []
        active_radii = []

        for sid in store_ids:
            try:
                if sunday not in sol.get(sid, []):
                    continue
                radius = float(data[sid].get("radius_km", 0) or 0)
                if radius <= 0:
                    continue
                active_coords.append(data[sid]["coordinates"])
                active_radii.append(radius)
            except Exception:
                continue

        if not active_coords:
            per_sunday.append(0.0)
            continue

        try:
            boxes = fast_create_boxes(active_coords, np.array(active_radii))
            union, intersect = fast_union_intersect(boxes)
            per_sunday.append(float(union - intersect))
        except Exception:
            per_sunday.append(0.0)

    overall = sum(per_sunday) / max(1, len(per_sunday))
    return per_sunday, overall


def _build_stats(
    rand_per: list[float],
    rand_overall: float,
    opt_per: list[float],
    opt_overall: float,
    delta_per: list[float],
) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "overall": {
            "random": rand_overall,
            "optimized": opt_overall,
            "delta": opt_overall - rand_overall,
        },
        "per_sunday": [
            {
                "sunday": i,
                "random": rand_per[i],
                "optimized": opt_per[i],
                "delta": delta_per[i],
            }
            for i in range(len(delta_per))
        ],
    }

    arr = np.array(delta_per)
    if arr.size == 0:
        stats["delta_summary"] = {"sum": 0.0, "mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
    else:
        stats["delta_summary"] = {
            "sum": float(np.sum(arr)),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
        }

    stats["per_sunday_pct"] = [
        None if r == 0 else (o - r) / abs(r) * 100.0
        for r, o in zip(rand_per, opt_per)
    ]
    return stats


def _write_status(
    results_dir: Path,
    state: str,
    random_name: str,
    optimized_name: str,
    error: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "state": state,
        "random_name": random_name,
        "optimized_name": optimized_name,
        "updated_at": _utc_now(),
    }
    if error:
        payload["error"] = error

    try:
        jobCreationService._write_json(results_dir / STATS_STATUS_FILE, payload)
    except Exception:
        pass


def _mtime(path: Path) -> float | None:
    return path.stat().st_mtime if path.exists() else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
