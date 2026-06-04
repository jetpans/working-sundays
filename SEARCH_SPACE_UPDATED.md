# Simplified Hyperparameter Search Space with Fixed Operators

## Overview

The search space now **ALWAYS uses fixed composite operators** with specific types assigned to each child:

- **Mutator**: CompositeMutator(RandomSimpleMutator #1, RandomSimpleMutator #2)
- **Crossover**: CompositeCrossover(GeometricColumnCrossover, KSwitchCrossover)
- **Generator**: CompositeGenerator(RandomGenerator, SeedingGenerator)

This eliminates wasted categorical dimensions and reduces the search space from 48 to **27 hyperparameters** (28 with deterministic flag).

---

## Search Space Structure

---

## Search Space Structure

### General Settings (2)
- `general_MAX_CLUSTER_DISTANCE`: Real [1.0, 12.0]
- `general_MAX_CLUSTER_JOIN_DISTANCE`: Real [2.0, 20.0]

### GA Base Parameters (5)
- `populationSize`: Integer [40, 300]
- `generations`: Integer [500, 8000]
- `newChromosomes`: Integer [1, 8]
- `elitism`: Integer [1, 20]
- `numThreads`: Integer [1, 8]

### MUTATOR (7) - **ALWAYS CompositeMutator with 2x RandomSimpleMutator**
```
CompositeMutator(
    p: mutator_comp_p,
    children: [
        {
            type: "RandomSimpleMutator",  ← FIXED
            params: {
                numMutations: mutator_child1_numMutations,
                p: mutator_child1_p
            },
            weight: mutator_child1_weight
        },
        {
            type: "RandomSimpleMutator",  ← FIXED
            params: {
                numMutations: mutator_child2_numMutations,
                p: mutator_child2_p
            },
            weight: mutator_child2_weight
        }
    ]
)
```

**Hyperparameters (7):**
1. `mutator_comp_p`: Real [0.1, 1.0]
2. `mutator_child1_numMutations`: Integer [1, 10]
3. `mutator_child1_p`: Real [0.1, 0.9]
4. `mutator_child1_weight`: Real [0.1, 1.0]
5. `mutator_child2_numMutations`: Integer [1, 10]
6. `mutator_child2_p`: Real [0.1, 0.9]
7. `mutator_child2_weight`: Real [0.1, 1.0]

✓ **Removed**: `mutator_child1_type` and `mutator_child2_type` (no longer categorical choices)

### CROSSOVER (7) - **ALWAYS CompositeCrossover with GeometricColumnCrossover + KSwitchCrossover**
```
CompositeCrossover(
    p: crossover_comp_p,
    children: [
        {
            type: "GeometricColumnCrossover",  ← FIXED
            params: {
                geoP: crossover_child1_geoP,
                crossoverProb: crossover_child1_crossoverProb
            },
            weight: crossover_child1_weight
        },
        {
            type: "KSwitchCrossover",  ← FIXED
            params: {
                k: crossover_child2_k,
                p: crossover_child2_p
            },
            weight: crossover_child2_weight
        }
    ]
)
```

**Hyperparameters (7):**
1. `crossover_comp_p`: Real [0.1, 1.0]
2. `crossover_child1_geoP`: Real [0.1, 0.8] (GeometricColumnCrossover param)
3. `crossover_child1_crossoverProb`: Real [0.1, 0.95] (GeometricColumnCrossover param)
4. `crossover_child1_weight`: Real [0.1, 1.0]
5. `crossover_child2_k`: Integer [2, 8] (KSwitchCrossover param)
6. `crossover_child2_p`: Real [0.1, 0.9] (KSwitchCrossover param)
7. `crossover_child2_weight`: Real [0.1, 1.0]

**Optimization**: Removed non-applicable parameters:
- ✓ No `crossover_child1_k`, `crossover_child1_p` (not used by GeometricColumnCrossover)
- ✓ No `crossover_child2_geoP`, `crossover_child2_crossoverProb` (not used by KSwitchCrossover)
- ✓ No type categorical dimensions (`crossover_child1_type`, `crossover_child2_type`)

### GENERATOR (2) - **ALWAYS CompositeGenerator with RandomGenerator + SeedingGenerator**
```
CompositeGenerator(
    children: [
        {
            type: "RandomGenerator",  ← FIXED
            params: {},
            weight: generator_child1_weight
        },
        {
            type: "SeedingGenerator",  ← FIXED
            params: {},
            weight: generator_child2_weight
        }
    ]
)
```

**Hyperparameters (2):**
1. `generator_child1_weight`: Real [0.1, 1.0]
2. `generator_child2_weight`: Real [0.1, 1.0]

✓ **Removed**: `generator_child1_type` and `generator_child2_type` (no longer categorical choices)

### SELECTION (2)
- `selection_type`: Categorical ["TournamentSelection", "RankSelection"]
- `selection_tournamentSize`: Integer [2, 6] (for TournamentSelection)

### FITNESS (1)
- `fitness_type`: Categorical ["FastIntersectUnionFitness", "CorrectFitness"]

### LOGGER (1)
- `logger_type`: Categorical ["SoutLogger"]

### Optional (1)
- `deterministic`: Categorical [True, False] ← Optional, controlled by `include_deterministic`

---

## Dimension Breakdown

| Category | Count | Details |
|----------|-------|---------|
| General Settings | 2 | MAX_CLUSTER_DISTANCE, MAX_CLUSTER_JOIN_DISTANCE |
| GA Base Params | 5 | populationSize, generations, newChromosomes, elitism, numThreads |
| Mutator | 7 | comp_p + 2×(child: numMutations, p, weight) |
| Crossover | 7 | comp_p + child1(geoP, crossoverProb, weight) + child2(k, p, weight) |
| Generator | 2 | 2× weight only (types are fixed) |
| Selection | 2 | type (TournamentSelection or RankSelection) + tournamentSize |
| Fitness | 1 | type (FastIntersectUnionFitness or CorrectFitness) |
| Logger | 1 | type (SoutLogger) |
| **Total** | **27** | All non-optional |
| Optional | 1 | deterministic (True/False) |
| **Total with deterministic** | **28** | |

---

## Why This Simplified Design Works

1. ✅ **No wasted dimensions**: Previous design had type categoricals that could lead to unused parameter branches
2. ✅ **Smaller, cleaner search space**: 27 dims vs 48 dims = 44% reduction
3. ✅ **Bayesian optimizer efficiency**: Fewer dimensions = better convergence and faster optimization
4. ✅ **Every sample is valid**: No conditional branching in configuration building
5. ✅ **Focused exploration**: Search can invest in operator-specific parameters rather than type choices
6. ✅ **Fixed, well-chosen operators**:
   - Mutator: Both children use RandomSimpleMutator (only option)
   - Crossover: Mixes geometric (column-based) and k-switch (structured) approaches
   - Generator: Mixes random and seeding strategies

---

## Example Generated Configuration

Given a sample from 27 dimensions:
```json
{
  "populationSize": 150,
  "generations": 3000,
  "newChromosomes": 4,
  "elitism": 10,
  "numThreads": 4,
  
  "mutator": {
    "type": "CompositeMutator",
    "params": {
      "p": 0.8,
      "children": [
        {
          "type": "RandomSimpleMutator",
          "params": { "numMutations": 5, "p": 0.5 },
          "weight": 0.7
        },
        {
          "type": "RandomSimpleMutator",
          "params": { "numMutations": 3, "p": 0.6 },
          "weight": 0.3
        }
      ]
    }
  },
  
  "crossover": {
    "type": "CompositeCrossover",
    "params": {
      "p": 0.85,
      "children": [
        {
          "type": "GeometricColumnCrossover",
          "params": { "geoP": 0.5, "crossoverProb": 0.8 },
          "weight": 0.6
        },
        {
          "type": "KSwitchCrossover",
          "params": { "k": 4, "p": 0.5 },
          "weight": 0.4
        }
      ]
    }
  },
  
  "generator": {
    "type": "CompositeGenerator",
    "params": {
      "children": [
        {
          "type": "RandomGenerator",
          "params": {},
          "weight": 0.5
        },
        {
          "type": "SeedingGenerator",
          "params": {},
          "weight": 0.5
        }
      ]
    }
  },
  
  "selection": {
    "type": "TournamentSelection",
    "params": { "tournamentSize": 4 }
  },
  
  "fitness": {
    "type": "CorrectFitness",
    "params": {}
  },
  
  "logger": {
    "type": "SoutLogger",
    "params": {}
  }
}
```

---

## Key Changes from Previous Design

| Aspect | Old (48 dims) | New (27 dims) | Reduction |
|--------|---------------|---------------|-----------|
| **Mutator types** | Type choice: Simple vs Composite | Always Composite (fixed) | -2 cat |
| **Mutator setup** | 9 dims (with unused choices) | 7 dims (no waste) | -2 dims |
| **Crossover types** | Type choice among 5 base + Composite | Fixed: GeometricColumnCrossover + KSwitchCrossover | -2 cat |
| **Crossover setup** | 18 dims (many unused per type) | 7 dims (only relevant params) | -11 dims |
| **Generator types** | Type choice among 3 base + Composite | Fixed: RandomGenerator + SeedingGenerator | -2 cat |
| **Generator setup** | 4 dims | 2 dims (only weights) | -2 dims |
| **Total hyperparameters** | 48 | 27 | **-21 dims (44% reduction)** |

**Benefit**: Every hyperparameter is always active and relevant. No categorical choices creating unused branches.

---

## Testing & Validation

Run hyperparameter tuning with the simplified search space:

```bash
cd hyperparameter-optimization
python main.py
```

The optimizer will:
1. Sample from the 27-dimensional space
2. Build fixed composite configurations for every sample
3. Evaluate on template instances
4. Discover patterns in operator parameter tuning

All 27 hyperparameters are active and contribute to optimization.

---

## Implementation Files

- **[search_space.py](hyperparameter-optimization/search_space.py)** — Core search space definition + builders
  - `build_search_space()` — 27 dimensions
  - `build_mutator_child()`, `build_crossover_child()`, `build_generator_child()` — Fixed-type builders
  - `build_ga_settings()` — Creates CompositeMutator/CompositeCrossover/CompositeGenerator configs

No changes needed in `main.py`, `api_client.py`, or backend API.
