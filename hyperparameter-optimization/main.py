from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple
import json
import csv
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from skopt import Optimizer
from skopt.space import Categorical, Integer, Real

from api_client import ApiClient, ApiError
from config import CONFIG
from search_space import build_search_space, build_settings_payload, build_settings_key


@dataclass
class InstanceTemplate:
    path: Path
    descriptor: Dict[str, Any]
    data: Dict[str, Any]
    constraints: Dict[str, Any]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def load_instance_template(path: Path) -> InstanceTemplate:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "descriptor" in raw:
        payload = raw["descriptor"]
    else:
        payload = raw

    data = payload.get("data")
    constraints = payload.get("constraints")
    descriptor = dict(payload)

    if data is None or constraints is None:
        raise ValueError(f"Template {path} missing data or constraints")

    descriptor.pop("data", None)
    descriptor.pop("constraints", None)

    return InstanceTemplate(path=path, descriptor=descriptor, data=data, constraints=constraints)


def build_optimizer() -> Tuple[Optimizer, List[str], List[Any]]:
    specs = build_search_space()
    dimensions = [spec.dim for spec in specs]
    names = [spec.name for spec in specs]
    optimizer = Optimizer(
        dimensions=dimensions,
        random_state=CONFIG.random_seed,
        n_initial_points=CONFIG.n_initial,
        acq_func="gp_hedge",
    )
    return optimizer, names, dimensions


def materialize_job(
    client: ApiClient,
    template: InstanceTemplate,
    general: Dict[str, Any],
    ga: Dict[str, Any],
    description: str | None = None,
) -> str:
    job_id = client.create_job()

    base_settings = template.descriptor.get("settings", {})
    base_general = base_settings.get("general", {})
    base_ga = base_settings.get("ga", {})

    merged_general = {**base_general, **general}
    merged_ga = {**base_ga, **ga}

    client.load_settings(job_id, {"general": merged_general, "ga": merged_ga})

    radius_calc = template.descriptor.get("value_for_radius_calculator")
    if radius_calc:
        client.load_stores_with_radius(job_id, template.data, radius_calc)
    else:
        client.load_stores(job_id, template.data)

    client.load_constraints(job_id, template.constraints)

    calc = template.descriptor.get("value_calculator")
    if calc:
        client.load_calc(job_id, calc)

    if description:
        # attach a human-readable description so server shows this was HPO-driven
        try:
            client.load_description(job_id, description)
        except Exception:
            # non-fatal: description is a nicety, don't fail the run for it
            pass

    return job_id


def extract_fitness(solution_payload: Dict[str, Any], fitness_key: str) -> float:
    if isinstance(solution_payload, dict) and fitness_key in solution_payload:
        return float(solution_payload[fitness_key])
    raise ValueError(f"Expected '{fitness_key}' in solution payload")


def log_to_csv(
    csv_path: Path,
    iteration: int,
    sample: Dict[str, Any],
    avg_fitness: float,
    per_template_scores: List[Tuple[str, float]],
) -> None:
    """Log tested configuration to CSV with template-specific columns."""
    file_exists = csv_path.exists()
    
    # Flatten params for CSV
    row = {
        "iteration": iteration,
        "timestamp": utc_now().isoformat(),
        "avg_fitness": avg_fitness,
    }
    
    # Add all hyperparams
    row.update(sample)
    
    # Add per-template scores using template names
    for template_name, score in per_template_scores:
        row[f"{template_name}_fitness"] = score
    
    try:
        with csv_path.open("a", newline="", encoding="utf-8") as f:
            fieldnames = list(row.keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(row)
    except Exception as e:
        print(f"Warning: Failed to log to CSV: {e}")


def append_to_cache(
    cache_path: Path,
    iteration: int,
    sample: Dict[str, Any],
    avg_fitness: float,
    per_template_scores: List[Tuple[str, float]],
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    log_to_csv(cache_path, iteration, sample, avg_fitness, per_template_scores)


def bootstrap_cache_if_needed(cache_path: Path, bootstrap_path: Path) -> None:
    if cache_path.exists():
        return
    if not bootstrap_path.exists():
        print(f"Cache not found and bootstrap CSV missing: {bootstrap_path}")
        return

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with bootstrap_path.open("r", newline="", encoding="utf-8") as source:
            with cache_path.open("w", newline="", encoding="utf-8") as target:
                target.write(source.read())
        print(f"Bootstrapped HPO cache from {bootstrap_path}")
    except Exception as e:
        print(f"Warning: Failed to bootstrap HPO cache from {bootstrap_path}: {e}")


def parse_dimension_value(raw_value: str, dimension: Any) -> Any:
    if raw_value is None or raw_value == "":
        raise ValueError("missing value")

    if isinstance(dimension, Integer):
        return int(float(raw_value))
    if isinstance(dimension, Real):
        return float(raw_value)
    if isinstance(dimension, Categorical):
        categories = list(dimension.categories)
        for category in categories:
            if str(category) == raw_value:
                return category
        raise ValueError(f"{raw_value!r} is not in {categories!r}")

    return raw_value


def parse_cached_sample(
    row: Dict[str, str],
    names: Sequence[str],
    dimensions: Sequence[Any],
) -> Tuple[List[Any], Dict[str, Any], float]:
    point: List[Any] = []
    sample: Dict[str, Any] = {}

    for name, dimension in zip(names, dimensions):
        if name not in row:
            raise ValueError(f"missing column {name}")
        value = parse_dimension_value(row[name], dimension)
        point.append(value)
        sample[name] = value

    if "avg_fitness" not in row:
        raise ValueError("missing column avg_fitness")

    avg_fitness = float(row["avg_fitness"])
    return point, sample, avg_fitness


def load_cached_observations(
    cache_path: Path,
    names: Sequence[str],
    dimensions: Sequence[Any],
    template_ga: Dict[str, Any],
) -> Tuple[List[List[Any]], List[float], Dict[str, Dict[str, Any]], Dict[str, Any]]:
    points: List[List[Any]] = []
    objectives: List[float] = []
    samples_by_key: Dict[str, Dict[str, Any]] = {}
    best: Dict[str, Any] = {"score": None, "params": None}
    skipped = 0

    if not cache_path.exists():
        return points, objectives, samples_by_key, best

    try:
        with cache_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_number, row in enumerate(reader, start=2):
                try:
                    point, sample, avg_fitness = parse_cached_sample(row, names, dimensions)
                    canonical_key = build_settings_key(sample, template_ga)
                    if canonical_key in samples_by_key:
                        skipped += 1
                        print(f"Warning: Skipping duplicate cache row {row_number}")
                        continue

                    points.append(point)
                    objectives.append(-avg_fitness)
                    samples_by_key[canonical_key] = sample
                    if best["score"] is None or avg_fitness > best["score"]:
                        best = {"score": avg_fitness, "params": sample}
                except Exception as e:
                    skipped += 1
                    print(f"Warning: Skipping incompatible cache row {row_number}: {e}")
    except Exception as e:
        print(f"Warning: Failed to load HPO cache {cache_path}: {e}")
        return [], [], {}, {"score": None, "params": None}

    print(f"Loaded {len(points)} cached HPO observations from {cache_path}")
    if skipped:
        print(f"Skipped {skipped} cache rows")

    return points, objectives, samples_by_key, best


def save_best_params(
    best_params_path: Path,
    iteration: int,
    best_params: Dict[str, Any],
    best_score: float,
) -> None:
    """Save best params snapshot for quick reference."""
    try:
        best_params_path.write_text(
            json.dumps({
                "iteration": iteration,
                "timestamp": utc_now().isoformat(),
                "best_score": best_score,
                "params": best_params,
            }, indent=2),
            encoding="utf-8"
        )
    except Exception as e:
        print(f"Warning: Failed to save best params: {e}")


def ask_unique_candidates(
    optimizer: Optimizer,
    names: List[str],
    seen_keys: set[str],
    batch_size: int,
    template_ga: Dict[str, Any],
) -> List[Tuple[List[Any], Dict[str, Any], str]]:
    candidates: List[Tuple[List[Any], Dict[str, Any], str]] = []
    batch_keys: set[str] = set()
    attempts = 0
    max_attempts = 100

    while len(candidates) < batch_size and attempts < max_attempts:
        needed = batch_size - len(candidates)
        points = optimizer.ask(n_points=needed)
        if needed == 1 and not isinstance(points[0], list):
            points = [points]

        for point in points:
            sample = {name: value for name, value in zip(names, point)}
            key = build_settings_key(sample, template_ga)
            if key in seen_keys or key in batch_keys:
                continue
            candidates.append((point, sample, key))
            batch_keys.add(key)

        attempts += 1

    if len(candidates) < batch_size:
        raise RuntimeError("Unable to find enough new unique configurations to evaluate")

    return candidates


def evaluate_candidate(
    client: ApiClient,
    templates: List[InstanceTemplate],
    sample: Dict[str, Any],
    run_number: int,
    log_path: Path,
) -> Tuple[float, str, List[Tuple[str, float]]]:
    """
    Evaluate a candidate configuration on all templates.
    
    Returns:
        Tuple of (average_fitness, canonical_key, list of (template_name, fitness) tuples)
    """
    scores: List[Tuple[str, float]] = []
    template_ga = templates[0].descriptor.get("settings", {}).get("ga", {})
    canonical_key = build_settings_key(sample, template_ga)

    for template in templates:
        job_id = None
        template_name = template.path.name
        try:
            base_general = template.descriptor.get("settings", {}).get("general", {})
            base_ga = template.descriptor.get("settings", {}).get("ga", {})
            general, ga, _ = build_settings_payload(sample, base_general, base_ga)
            desc = f"HPO#{run_number}"
            job_id = materialize_job(client, template, general, ga, description=desc)
            # Log the job creation and params
            try:
                with log_path.open("a", encoding="utf-8") as lf:
                    lf.write(
                        f"{utc_now().isoformat()} - Run {run_number} - template {template_name} - job {job_id} - params: {json.dumps(sample)}\n")
            except Exception:
                pass
            client.run_job(job_id)
            status = client.wait_for_run(job_id, CONFIG.poll_interval_sec)
            if status.status != "Complete":
                raise ApiError(f"Run failed with status {status.status}")

            result = client.get_job_result(job_id)
            solution = result.get("solution")
            if solution is None:
                raise ApiError("Result payload missing solution")
            used_source = "solution"
            try:
                fitness = extract_fitness(solution, CONFIG.results_fitness_key)
            except ValueError:
                # Fallback to computed stats. Prefer optimized value to match server's reported optimized metric.
                stats = client.get_results_stats(job_id)
                overall = stats.get("overall", {})
                if "optimized" in overall:
                    fitness = float(overall["optimized"])
                    used_source = "stats.optimized"
                elif "delta" in overall:
                    fitness = float(overall["delta"])
                    used_source = "stats.delta"
                else:
                    raise ApiError(f"Unable to extract fitness from result or stats for job {job_id}")

            # Log the fitness value and source
            try:
                with log_path.open("a", encoding="utf-8") as lf:
                    lf.write(
                        f"{utc_now().isoformat()} - Run {run_number} - job {job_id} - fitness_source: {used_source} - fitness: {fitness}\n")
            except Exception:
                pass
            scores.append((template_name, fitness))
        finally:
            # Do not delete jobs; keep them for later inspection.
            pass

    if not scores:
        raise RuntimeError("No scores returned from evaluation")

    avg_score = sum(score for _, score in scores) / len(scores)
    return avg_score, canonical_key, scores


def main() -> None:
    templates = [
        load_instance_template(path)
        for path in sorted(CONFIG.instances_dir.glob("*.job"))
    ]
    if not templates:
        raise RuntimeError(
            f"No .job templates found in {CONFIG.instances_dir}. Export from the UI and place them here."
        )

    client = ApiClient(CONFIG.api_base_url, CONFIG.username, CONFIG.password)
    client.login()

    optimizer, names, dimensions = build_optimizer()

    # Prepare logging
    hpo_dir = Path(__file__).resolve().parent
    log_dir = hpo_dir / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
    text_logfile = f"hpo_{timestamp}.txt"
    csv_logfile = f"hpo_{timestamp}.csv"
    best_params_file = f"best_params_{timestamp}.json"
    
    text_log_path = log_dir / text_logfile
    csv_log_path = log_dir / csv_logfile
    best_params_path = log_dir / best_params_file
    cache_path = CONFIG.cache_csv
    cache_bootstrap_path = CONFIG.cache_bootstrap_csv
    template_ga = templates[0].descriptor.get("settings", {}).get("ga", {})

    bootstrap_cache_if_needed(cache_path, cache_bootstrap_path)
    cached_points, cached_objectives, cached_samples, cached_best = load_cached_observations(
        cache_path,
        names,
        dimensions,
        template_ga,
    )
    if cached_points:
        optimizer.tell(cached_points, cached_objectives)
    
    try:
        with text_log_path.open("a", encoding="utf-8") as lf:
            lf.write(f"HPO started at {utc_now().isoformat()}\n")
            lf.write(f"Templates: {', '.join(t.path.name for t in templates)}\n")
            lf.write(f"Search space dimensions: {len(names)}\n")
            lf.write(f"Candidate batch size: {CONFIG.candidate_batch_size}\n")
            lf.write(f"Cache CSV: {cache_path}\n")
            lf.write(f"Loaded cached observations: {len(cached_points)}\n")
    except Exception:
        pass

    best_score = cached_best["score"]
    best_params = cached_best["params"]
    seen_keys = set(cached_samples.keys())

    completed_candidates = 0
    cache_iteration_start = len(cached_points)

    if cached_points:
        print(
            f"Starting HPO with {len(cached_points)} cached observations "
            f"and {CONFIG.max_iter} new candidates planned"
        )

    while completed_candidates < CONFIG.max_iter:
        batch_size = min(CONFIG.candidate_batch_size, CONFIG.max_iter - completed_candidates)
        candidates = ask_unique_candidates(
            optimizer,
            names,
            seen_keys,
            batch_size,
            template_ga,
        )

        print(
            f"Starting batch of {len(candidates)} candidates "
            f"({completed_candidates + 1}-{completed_candidates + len(candidates)}/{CONFIG.max_iter} new, "
            f"{len(cached_points)} cached)"
        )

        batch_results: List[Tuple[int, List[Any], Dict[str, Any], str, float, List[Tuple[str, float]]]] = []
        with ThreadPoolExecutor(max_workers=len(candidates)) as executor:
            future_to_candidate = {
                executor.submit(
                    evaluate_candidate,
                    client,
                    templates,
                    sample,
                    completed_candidates + index + 1,
                    text_log_path,
                ): (index, point, sample, canonical_key)
                for index, (point, sample, canonical_key) in enumerate(candidates)
            }

            for future in as_completed(future_to_candidate):
                index, point, sample, expected_key = future_to_candidate[future]
                score, canonical_key, per_template_scores = future.result()
                if canonical_key != expected_key:
                    raise RuntimeError("Candidate key changed during evaluation")
                batch_results.append((index, point, sample, canonical_key, score, per_template_scores))

        batch_results.sort(key=lambda result: result[0])

        points = []
        objectives = []
        for index, point, sample, canonical_key, score, per_template_scores in batch_results:
            iteration = completed_candidates + index + 1
            cache_iteration = cache_iteration_start + iteration
            seen_keys.add(canonical_key)
            log_to_csv(csv_log_path, iteration, sample, score, per_template_scores)
            append_to_cache(cache_path, cache_iteration, sample, score, per_template_scores)

            points.append(point)
            objectives.append(-score)

            if best_score is None or score > best_score:
                best_score = score
                best_params = sample
                save_best_params(best_params_path, cache_iteration, best_params, best_score)

            print(
                f"Iter {iteration}/{CONFIG.max_iter} new "
                f"(cache #{cache_iteration}): score={score:.6f} best={best_score:.6f}"
            )

        optimizer.tell(points, objectives)
        completed_candidates += len(batch_results)

    print("\nBest score:", best_score)
    print("Best params:")
    print(json.dumps(best_params, indent=2))
    print(f"\nResults logged to:")
    print(f"  CSV: {csv_log_path}")
    print(f"  Cache: {cache_path}")
    print(f"  Best params: {best_params_path}")
    print(f"  Text log: {text_log_path}")


if __name__ == "__main__":
    main()
