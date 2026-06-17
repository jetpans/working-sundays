from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    api_base_url: str
    username: str
    password: str
    instances_dir: Path
    poll_interval_sec: float
    run_timeout_sec: float
    max_iter: int
    candidate_batch_size: int
    n_initial: int
    random_seed: int
    deterministic_default: bool
    results_fitness_key: str


ROOT_DIR = Path(__file__).resolve().parent


CONFIG = AppConfig(
    api_base_url=os.getenv("API_BASE_URL", "http://localhost:5000"),
    username=os.getenv("API_USERNAME", ""),
    password=os.getenv("API_PASSWORD", ""),
    instances_dir=Path(os.getenv("HPO_INSTANCES_DIR", str(ROOT_DIR / "instances"))),
    poll_interval_sec=float(os.getenv("POLL_INTERVAL_SEC", "2.0")),
    run_timeout_sec=float(os.getenv("RUN_TIMEOUT_SEC", "3600")),
    max_iter=int(os.getenv("MAX_ITER", "20")),
    candidate_batch_size=max(1, int(os.getenv("CANDIDATE_BATCH_SIZE", "1"))),
    n_initial=int(os.getenv("N_INITIAL", "5")),
    random_seed=int(os.getenv("RANDOM_SEED", "42")),
    deterministic_default=os.getenv("DETERMINISTIC_DEFAULT", "true").lower() == "true",
    results_fitness_key=os.getenv("RESULTS_FITNESS_KEY", "fitness"),
)
