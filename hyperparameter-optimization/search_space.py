from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import copy
import json

from skopt.space import Categorical, Integer, Real


@dataclass(frozen=True)
class SpaceSpec:
    name: str
    dim: Any


MUTATOR_BASE = ["RandomSimpleMutator"]
MUTATOR_TYPES = MUTATOR_BASE + ["CompositeMutator"]

CROSSOVER_BASE = [
    "GeometricColumnCrossover",
    "GeometricRowCrossover",
    "SinglePointCrossover",
    "KSwitchCrossover",
    "ColumnKSwitchCrossover",
]
CROSSOVER_TYPES = CROSSOVER_BASE + ["CompositeCrossover"]

GENERATOR_BASE = [
    "AllSundaysHaveWorkGenerator",
    "RandomGenerator",
    "SeedingGenerator",
]
GENERATOR_TYPES = GENERATOR_BASE + ["CompositeGenerator"]


def build_search_space(include_deterministic: bool = True) -> List[SpaceSpec]:
    specs: List[SpaceSpec] = [
        SpaceSpec("general_MAX_CLUSTER_DISTANCE", Real(1.0, 12.0)),
        SpaceSpec("general_MAX_CLUSTER_JOIN_DISTANCE", Real(2.0, 20.0)),
        SpaceSpec("populationSize", Integer(40, 300)),
        SpaceSpec("generations", Integer(500, 8000)),
        SpaceSpec("newChromosomes", Integer(1, 8)),
        SpaceSpec("elitism", Integer(1, 20)),
        SpaceSpec("numThreads", Integer(1, 8)),
        SpaceSpec("mutator_type", Categorical(MUTATOR_TYPES)),
        SpaceSpec("mutator_numMutations", Integer(1, 10)),
        SpaceSpec("mutator_p", Real(0.1, 0.9)),
        SpaceSpec("mutator_comp_p", Real(0.1, 1.0)),
        SpaceSpec("mutator_child1_type", Categorical(MUTATOR_BASE)),
        SpaceSpec("mutator_child1_numMutations", Integer(1, 10)),
        SpaceSpec("mutator_child1_p", Real(0.1, 0.9)),
        SpaceSpec("mutator_child1_weight", Real(0.1, 1.0)),
        SpaceSpec("mutator_child2_type", Categorical(MUTATOR_BASE)),
        SpaceSpec("mutator_child2_numMutations", Integer(1, 10)),
        SpaceSpec("mutator_child2_p", Real(0.1, 0.9)),
        SpaceSpec("mutator_child2_weight", Real(0.1, 1.0)),
        SpaceSpec(
            "crossover_type",
            Categorical(CROSSOVER_TYPES),
        ),
        SpaceSpec("crossover_geoP", Real(0.1, 0.8)),
        SpaceSpec("crossover_crossoverProb", Real(0.1, 0.95)),
        SpaceSpec("crossover_k", Integer(2, 8)),
        SpaceSpec("crossover_p", Real(0.1, 0.9)),
        SpaceSpec("crossover_comp_p", Real(0.1, 1.0)),
        SpaceSpec("crossover_child1_type", Categorical(CROSSOVER_BASE)),
        SpaceSpec("crossover_child1_geoP", Real(0.1, 0.8)),
        SpaceSpec("crossover_child1_crossoverProb", Real(0.1, 0.95)),
        SpaceSpec("crossover_child1_k", Integer(2, 8)),
        SpaceSpec("crossover_child1_p", Real(0.1, 0.9)),
        SpaceSpec("crossover_child1_weight", Real(0.1, 1.0)),
        SpaceSpec("crossover_child2_type", Categorical(CROSSOVER_BASE)),
        SpaceSpec("crossover_child2_geoP", Real(0.1, 0.8)),
        SpaceSpec("crossover_child2_crossoverProb", Real(0.1, 0.95)),
        SpaceSpec("crossover_child2_k", Integer(2, 8)),
        SpaceSpec("crossover_child2_p", Real(0.1, 0.9)),
        SpaceSpec("crossover_child2_weight", Real(0.1, 1.0)),
        SpaceSpec("selection_type", Categorical(["TournamentSelection", "RankSelection"])),
        SpaceSpec("selection_tournamentSize", Integer(2, 6)),
        SpaceSpec("fitness_type", Categorical(["FastIntersectUnionFitness", "CorrectFitness"])),
        SpaceSpec(
            "generator_type",
            Categorical(GENERATOR_TYPES),
        ),
        SpaceSpec("generator_child1_type", Categorical(GENERATOR_BASE)),
        SpaceSpec("generator_child1_weight", Real(0.1, 1.0)),
        SpaceSpec("generator_child2_type", Categorical(GENERATOR_BASE)),
        SpaceSpec("generator_child2_weight", Real(0.1, 1.0)),
        SpaceSpec("logger_type", Categorical(["SoutLogger"])),
    ]

    if include_deterministic:
        specs.append(SpaceSpec("deterministic", Categorical([True, False])))

    return specs


def build_mutator_child(sample: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    child_type = sample[f"{prefix}_type"]
    params: Dict[str, Any] = {}
    if child_type == "RandomSimpleMutator":
        params = {
            "numMutations": int(sample[f"{prefix}_numMutations"]),
            "p": float(sample[f"{prefix}_p"]),
        }
    return {
        "type": child_type,
        "params": params,
        "weight": float(sample[f"{prefix}_weight"]),
    }


def build_crossover_child(sample: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    child_type = sample[f"{prefix}_type"]
    params: Dict[str, Any] = {}
    if child_type in {"GeometricColumnCrossover", "GeometricRowCrossover"}:
        params = {
            "geoP": float(sample[f"{prefix}_geoP"]),
            "crossoverProb": float(sample[f"{prefix}_crossoverProb"]),
        }
    elif child_type in {"KSwitchCrossover", "ColumnKSwitchCrossover"}:
        params = {
            "k": int(sample[f"{prefix}_k"]),
            "p": float(sample[f"{prefix}_p"]),
        }
    elif child_type == "SinglePointCrossover":
        params = {"p": float(sample[f"{prefix}_p"])}
    return {
        "type": child_type,
        "params": params,
        "weight": float(sample[f"{prefix}_weight"]),
    }


def build_generator_child(sample: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    return {
        "type": sample[f"{prefix}_type"],
        "params": {},
        "weight": float(sample[f"{prefix}_weight"]),
    }


def build_ga_settings(sample: Dict[str, Any]) -> Dict[str, Any]:
    mutator_type = sample["mutator_type"]
    if mutator_type == "CompositeMutator":
        mutator_params = {
            "p": float(sample["mutator_comp_p"]),
            "children": [
                build_mutator_child(sample, "mutator_child1"),
                build_mutator_child(sample, "mutator_child2"),
            ],
        }
    else:
        mutator_params = {
            "numMutations": int(sample["mutator_numMutations"]),
            "p": float(sample["mutator_p"]),
        }

    crossover_type = sample["crossover_type"]
    if crossover_type == "CompositeCrossover":
        crossover_params = {
            "p": float(sample["crossover_comp_p"]),
            "children": [
                build_crossover_child(sample, "crossover_child1"),
                build_crossover_child(sample, "crossover_child2"),
            ],
        }
    else:
        crossover_params: Dict[str, Any] = {}
        if crossover_type in {"GeometricColumnCrossover", "GeometricRowCrossover"}:
            crossover_params = {
                "geoP": float(sample["crossover_geoP"]),
                "crossoverProb": float(sample["crossover_crossoverProb"]),
            }
        elif crossover_type in {"KSwitchCrossover", "ColumnKSwitchCrossover"}:
            crossover_params = {
                "k": int(sample["crossover_k"]),
                "p": float(sample["crossover_p"]),
            }
        elif crossover_type == "SinglePointCrossover":
            crossover_params = {"p": float(sample["crossover_p"])}

    selection_type = sample["selection_type"]
    selection_params: Dict[str, Any] = {}
    if selection_type == "TournamentSelection":
        selection_params = {"tournamentSize": int(sample["selection_tournamentSize"])}

    generator_type = sample["generator_type"]
    if generator_type == "CompositeGenerator":
        generator_params = {
            "children": [
                build_generator_child(sample, "generator_child1"),
                build_generator_child(sample, "generator_child2"),
            ]
        }
    else:
        generator_params = {}

    ga = {
        "populationSize": int(sample["populationSize"]),
        "generations": int(sample["generations"]),
        "newChromosomes": int(sample["newChromosomes"]),
        "elitism": int(sample["elitism"]),
        "numThreads": int(sample["numThreads"]),
        "deterministic": bool(sample.get("deterministic", True)),
        "mutator": {"type": mutator_type, "params": mutator_params},
        "crossover": {"type": crossover_type, "params": crossover_params},
        "selection": {"type": selection_type, "params": selection_params},
        "fitness": {"type": sample["fitness_type"], "params": {}},
        "generator": {"type": generator_type, "params": generator_params},
        "logger": {"type": sample["logger_type"], "params": {}},
    }

    return ga


def build_general_settings(sample: Dict[str, Any], base_general: Dict[str, Any]) -> Dict[str, Any]:
    general = dict(base_general or {})
    general["MAX_CLUSTER_DISTANCE"] = float(sample["general_MAX_CLUSTER_DISTANCE"])
    general["MAX_CLUSTER_JOIN_DISTANCE"] = float(sample["general_MAX_CLUSTER_JOIN_DISTANCE"])
    return general


def build_settings_payload(sample: Dict[str, Any], base_general: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    general = build_general_settings(sample, base_general)
    ga = build_ga_settings(sample)
    key = json.dumps({"general": general, "ga": ga}, sort_keys=True, separators=(",", ":"))
    return general, ga, key


def build_settings_key(sample: Dict[str, Any]) -> str:
    general, ga, _ = build_settings_payload(sample, {})
    normalized = {
        "general": general,
        "ga": normalize_ga_for_key(ga),
    }
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def normalize_ga_for_key(ga: Dict[str, Any]) -> Dict[str, Any]:
    normalized = copy.deepcopy(ga)
    for key in ("mutator", "crossover", "generator"):
        node = normalized.get(key) or {}
        params = node.get("params") or {}
        children = params.get("children")
        if isinstance(children, list) and node.get("type", "").startswith("Composite"):
            children.sort(
                key=lambda child: json.dumps(child, sort_keys=True, separators=(",", ":"))
            )
    return normalized
