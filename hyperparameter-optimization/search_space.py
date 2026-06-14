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

CROSSOVER_BASE = [
    "GeometricColumnCrossover",
    "GeometricRowCrossover",
    "SinglePointCrossover",
    "KSwitchCrossover",
    "ColumnKSwitchCrossover",
]

GENERATOR_BASE = [
    "AllSundaysHaveWorkGenerator",
    "RandomGenerator",
    "SeedingGenerator",
]


def build_search_space() -> List[SpaceSpec]:
    """
    Build the hyperparameter search space with ALL operator types in composites.
    
    Key design:
    - Mutator: CompositeMutator with 2x RandomSimpleMutator (both with independent hyperparameters)
    - Crossover: CompositeCrossover with ALL 5 crossover types (each with its own hyperparameters and weight)
    - Generator: Fixed AllSundaysHaveWorkGenerator (only one available, no choice)
    - Selection: TournamentSelection or RankSelection (hyperparameter)
    
    Fixed settings (from job template): numThreads, logger, deterministic, fitness, timelimit, stagnation
    Goal: Include all types of mutators and crossovers in composites and optimize them together
    with weights for each child operator.
    
    Total dimensions: 34 hyperparameters
    Breakdown: General(2) + GA Base(4) + Eliminator(4) + Mutator(7) + Crossover(15) + Selection(2) = 34
    """
    specs: List[SpaceSpec] = [
        # General settings (2)
        SpaceSpec("general_MAX_CLUSTER_DISTANCE", Real(1.0, 12.0)),
        SpaceSpec("general_MAX_CLUSTER_JOIN_DISTANCE", Real(2.0, 20.0)),

        # GA base parameters (4) - numThreads now comes from job template
        SpaceSpec("populationSize", Categorical([50, 200, 500, 1000, 5000])),
        SpaceSpec("generations", Categorical([500, 2000, 5000, 8000])),
        SpaceSpec("newChromosomes", Integer(1, 30)),

        # ELIMINATOR: choose elimination strategy and its params (3)
        SpaceSpec("eliminator_type", Categorical(["EliteEliminator", "EliteGeometricEliminator"])),
        SpaceSpec("eliminator_elitism", Integer(1, 20)),
        SpaceSpec("eliminator_survivalRate", Real(0.05, 0.5)),
        SpaceSpec("eliminator_p", Real(0.1, 0.95)),

        # MUTATOR: CompositeMutator with 2x RandomSimpleMutator (7)
        # Both children are RandomSimpleMutator with independent hyperparameters
        SpaceSpec("mutator_comp_p", Real(1.0, 1.0)),
        SpaceSpec("mutator_child1_numMutations", Integer(1, 10)),
        SpaceSpec("mutator_child1_p", Real(0.1, 0.9)),
        SpaceSpec("mutator_child1_weight", Real(0.1, 1.0)),
        SpaceSpec("mutator_child2_numMutations", Integer(5, 20)),
        SpaceSpec("mutator_child2_p", Real(0.1, 0.9)),
        SpaceSpec("mutator_child2_weight", Real(0.1, 1.0)),

        # CROSSOVER: CompositeCrossover with ALL 5 base crossovers (15)
        SpaceSpec("crossover_comp_p", Real(1.0, 1.0)),

        # GeometricColumnCrossover (child1)
        SpaceSpec("crossover_child1_geoP", Real(0.1, 0.8)),
        SpaceSpec("crossover_child1_crossoverProb", Real(0.1, 0.95)),
        SpaceSpec("crossover_child1_weight", Real(0.1, 1.0)),

        # GeometricRowCrossover (child2)
        SpaceSpec("crossover_child2_geoP", Real(0.1, 0.8)),
        SpaceSpec("crossover_child2_crossoverProb", Real(0.1, 0.95)),
        SpaceSpec("crossover_child2_weight", Real(0.1, 1.0)),

        # SinglePointCrossover (child3)
        SpaceSpec("crossover_child3_p", Real(0.1, 0.9)),
        SpaceSpec("crossover_child3_weight", Real(0.1, 1.0)),

        # KSwitchCrossover (child4)
        SpaceSpec("crossover_child4_k", Integer(2, 8)),
        SpaceSpec("crossover_child4_p", Real(0.1, 0.9)),
        SpaceSpec("crossover_child4_weight", Real(0.1, 1.0)),

        # ColumnKSwitchCrossover (child5)
        SpaceSpec("crossover_child5_k", Integer(2, 8)),
        SpaceSpec("crossover_child5_p", Real(0.1, 0.9)),
        SpaceSpec("crossover_child5_weight", Real(0.1, 1.0)),

        # GENERATOR: Fixed AllSundaysHaveWorkGenerator (no hyperparameters)
        # Only one generator available, so no choice or weights to tune

        # Selection (2) - fitness, logger, deterministic, numThreads come from job template
        SpaceSpec("selection_type", Categorical(["TournamentSelection", "RankSelection"])),
        SpaceSpec("selection_tournamentSize", Integer(2, 6)),
    ]

    return specs


def build_mutator_child(sample: Dict[str, Any], child_num: int) -> Dict[str, Any]:
    """
    Build a mutator child. Both children are always RandomSimpleMutator.
    child_num: 1 or 2
    """
    prefix = f"mutator_child{child_num}"
    params = {
        "numMutations": int(sample[f"{prefix}_numMutations"]),
        "p": float(sample[f"{prefix}_p"]),
    }
    return {
        "type": "RandomSimpleMutator",
        "params": params,
        "weight": float(sample[f"{prefix}_weight"]),
    }


def build_crossover_child(sample: Dict[str, Any], child_num: int) -> Dict[str, Any]:
    """
    Build one crossover child from the fixed five-child composite.
    """
    if child_num == 1:
        params = {
            "geoP": float(sample["crossover_child1_geoP"]),
            "crossoverProb": float(sample["crossover_child1_crossoverProb"]),
        }
        return {
            "type": "GeometricColumnCrossover",
            "params": params,
            "weight": float(sample["crossover_child1_weight"]),
        }
    if child_num == 2:
        params = {
            "geoP": float(sample["crossover_child2_geoP"]),
            "crossoverProb": float(sample["crossover_child2_crossoverProb"]),
        }
        return {
            "type": "GeometricRowCrossover",
            "params": params,
            "weight": float(sample["crossover_child2_weight"]),
        }
    if child_num == 3:
        params = {
            "p": float(sample["crossover_child3_p"]),
        }
        return {
            "type": "SinglePointCrossover",
            "params": params,
            "weight": float(sample["crossover_child3_weight"]),
        }
    if child_num == 4:
        params = {
            "k": int(sample["crossover_child4_k"]),
            "p": float(sample["crossover_child4_p"]),
        }
        return {
            "type": "KSwitchCrossover",
            "params": params,
            "weight": float(sample["crossover_child4_weight"]),
        }
    params = {
        "k": int(sample["crossover_child5_k"]),
        "p": float(sample["crossover_child5_p"]),
    }
    return {
        "type": "ColumnKSwitchCrossover",
        "params": params,
        "weight": float(sample["crossover_child5_weight"]),
    }


def build_generator_child(sample: Dict[str, Any], child_num: int) -> Dict[str, Any]:
    """
    Build the fixed generator used by the search space.
    """
    return {
        "type": "AllSundaysHaveWorkGenerator",
        "params": {},
    }


def build_eliminator(sample: Dict[str, Any]) -> Dict[str, Any]:
    eliminator_type = sample["eliminator_type"]
    if eliminator_type == "EliteEliminator":
        return {
            "type": "EliteEliminator",
            "params": {
                "elitism": int(sample["eliminator_elitism"]),
            },
        }

    return {
        "type": "EliteGeometricEliminator",
        "params": {
            "survivalRate": float(sample["eliminator_survivalRate"]),
            "p": float(sample["eliminator_p"]),
        },
    }


def build_ga_settings(sample: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build GA settings with all operators included in composites, merged with template settings.
    
    Args:
        sample: Sampled hyperparameters (GA base, mutator, crossover, selection)
        template: Fixed settings from job template (numThreads, fitness, logger, deterministic, timelimit, stagnationFraction)
    
    Stagnation is calculated as: int(template["stagnationFraction"] * sample["generations"])
    """
    # MUTATOR: Always composite with 2x RandomSimpleMutator
    mutator_params = {
        "p": float(sample["mutator_comp_p"]),
        "children": [
            build_mutator_child(sample, 1),
            build_mutator_child(sample, 2),
        ],
    }

    # CROSSOVER: Always composite with ALL 5 crossover types
    crossover_params = {
        "p": float(sample["crossover_comp_p"]),
        "children": [
            build_crossover_child(sample, 1),
            build_crossover_child(sample, 2),
            build_crossover_child(sample, 3),
            build_crossover_child(sample, 4),
            build_crossover_child(sample, 5),
        ],
    }

    # SELECTION
    selection_type = sample["selection_type"]
    selection_params: Dict[str, Any] = {}
    if selection_type == "TournamentSelection":
        selection_params = {"tournamentSize": int(sample["selection_tournamentSize"])}

    # GENERATOR: Fixed AllSundaysHaveWorkGenerator (no hyperparameters)
    generator = build_generator_child(sample, 1)

    # Calculate stagnation based on generations and template stagnation fraction
    generations = int(sample["generations"])
    stagnation_fraction = float(template.get("stagnationFraction", 0.2))
    stagnation = int(stagnation_fraction * generations)

    ga = {
        "populationSize": int(sample["populationSize"]),
        "generations": generations,
        "newChromosomes": int(sample["newChromosomes"]),
        "numThreads": int(template.get("numThreads", 4)),
        "deterministic": bool(template.get("deterministic", False)),
        "eliminator": build_eliminator(sample),
        "mutator": {"type": "CompositeMutator", "params": mutator_params},
        "crossover": {"type": "CompositeCrossover", "params": crossover_params},
        "selection": {"type": selection_type, "params": selection_params},
        "fitness": {"type": template.get("fitness", "FastIntersectUnionFitness"), "params": {}},
        "generator": generator,
        "logger": {"type": template.get("logger", "SoutLogger"), "params": {}},
        "timelimit": int(template.get("timelimit", 3600)),
        "stagnation": stagnation,
    }

    return ga


def build_general_settings(sample: Dict[str, Any], base_general: Dict[str, Any]) -> Dict[str, Any]:
    general = dict(base_general or {})
    general["MAX_CLUSTER_DISTANCE"] = float(sample["general_MAX_CLUSTER_DISTANCE"])
    general["MAX_CLUSTER_JOIN_DISTANCE"] = float(sample["general_MAX_CLUSTER_JOIN_DISTANCE"])
    return general


def build_settings_payload(sample: Dict[str, Any], base_general: Dict[str, Any], template: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """Build settings payload by merging sampled hyperparameters with template settings.
    
    Args:
        sample: Sampled hyperparameters
        base_general: Base general settings (clustering distances, etc.)
        template: Fixed settings from job template
    """
    general = build_general_settings(sample, base_general)
    ga = build_ga_settings(sample, template)
    key = json.dumps({"general": general, "ga": ga}, sort_keys=True, separators=(",", ":"))
    return general, ga, key


def build_settings_key(sample: Dict[str, Any], template: Dict[str, Any]) -> str:
    general, ga, _ = build_settings_payload(sample, {}, template)
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
