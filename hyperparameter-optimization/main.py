from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
from datetime import datetime

from skopt import Optimizer

from api_client import ApiClient, ApiError
from config import CONFIG
from search_space import build_search_space, build_settings_payload, build_settings_key


@dataclass
class InstanceTemplate:
    path: Path
    descriptor: Dict[str, Any]
    data: Dict[str, Any]
    constraints: Dict[str, Any]


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


def build_optimizer() -> Tuple[Optimizer, List[str]]:
    specs = build_search_space()
    dimensions = [spec.dim for spec in specs]
    names = [spec.name for spec in specs]
    optimizer = Optimizer(
        dimensions=dimensions,
        random_state=CONFIG.random_seed,
        n_initial_points=CONFIG.n_initial,
        acq_func="gp_hedge",
    )
    return optimizer, names


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


def evaluate_candidate(
    client: ApiClient,
    templates: List[InstanceTemplate],
    sample: Dict[str, Any],
    run_number: int,
    log_path: Path,
) -> Tuple[float, str]:
    scores: List[float] = []
    template_ga = templates[0].descriptor.get("settings", {}).get("ga", {})
    canonical_key = build_settings_key(sample, template_ga)

    for template in templates:
        job_id = None
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
                        f"{datetime.utcnow().isoformat()} - Run {run_number} - template {template.path.name} - job {job_id} - params: {json.dumps(sample)}\n")
            except Exception:
                pass
            client.run_job(job_id)
            status = client.wait_for_run(
                job_id, CONFIG.run_timeout_sec, CONFIG.poll_interval_sec
            )
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
                        f"{datetime.utcnow().isoformat()} - Run {run_number} - job {job_id} - fitness_source: {used_source} - fitness: {fitness}\n")
            except Exception:
                pass
            scores.append(fitness)
        finally:
            # Do not delete jobs; keep them for later inspection.
            pass

    if not scores:
        raise RuntimeError("No scores returned from evaluation")

    return sum(scores) / len(scores), canonical_key


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

    optimizer, names = build_optimizer()

    # Prepare logging
    hpo_dir = Path(__file__).resolve().parent
    log_dir = hpo_dir / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    logfile = datetime.utcnow().strftime("hpo_%Y%m%d_%H%M%S.txt")
    log_path = log_dir / logfile
    # initial header
    try:
        with log_path.open("a", encoding="utf-8") as lf:
            lf.write(f"HPO started at {datetime.utcnow().isoformat()}\n")
    except Exception:
        pass

    best_score = None
    best_params = None
    seen_keys = set()

    for iteration in range(CONFIG.max_iter):
        sample = None
        point = None
        canonical_key = None
        template_ga = templates[0].descriptor.get("settings", {}).get("ga", {})
        for _ in range(100):
            point = optimizer.ask()
            candidate = {name: value for name, value in zip(names, point)}
            key = build_settings_key(candidate, template_ga)
            if key not in seen_keys:
                sample = candidate
                canonical_key = key
                break
        if sample is None or canonical_key is None:
            raise RuntimeError("Unable to find a new unique configuration to evaluate")

        score, canonical_key = evaluate_candidate(client, templates, sample, iteration + 1, log_path)
        seen_keys.add(canonical_key)

        objective = -score
        optimizer.tell(point, objective)

        if best_score is None or score > best_score:
            best_score = score
            best_params = sample

        print(
            f"Iter {iteration + 1}/{CONFIG.max_iter}: score={score:.6f} best={best_score:.6f}"
        )

    print("\nBest score:", best_score)
    print("Best params:")
    print(json.dumps(best_params, indent=2))


if __name__ == "__main__":
    main()
