# Complete Search Space: ALL Operators in Composites

## Summary

**Updated hyperparameter search space with all available operator types included:**

- ✅ **Mutator**: CompositeMutator with 2× RandomSimpleMutator (each with independent hyperparameters)
- ✅ **Crossover**: CompositeCrossover with ALL 5 crossover types (each with own hyperparameters and weight)
- ✅ **Generator**: Fixed AllSundaysHaveWorkGenerator (only available option, no choice needed)

**Total dimensions: 33** (34 with deterministic flag)

---

## Search Space Breakdown

### General Settings (2)
- `general_MAX_CLUSTER_DISTANCE`: Real [1.0, 12.0]
- `general_MAX_CLUSTER_JOIN_DISTANCE`: Real [2.0, 20.0]

### GA Base Parameters (5)
- `populationSize`: Integer [40, 300]
- `generations`: Integer [500, 8000]
- `newChromosomes`: Integer [1, 8]
- `elitism`: Integer [1, 20]
- `numThreads`: Integer [1, 8]

### MUTATOR: CompositeMutator (7 hyperparameters)

Both children are **RandomSimpleMutator** with independent hyperparameters:

```json
{
  "type": "CompositeMutator",
  "params": {
    "p": mutator_comp_p ∈ [0.1, 1.0],
    "children": [
      {
        "type": "RandomSimpleMutator",
        "params": {
          "numMutations": mutator_child1_numMutations ∈ [1, 10],
          "p": mutator_child1_p ∈ [0.1, 0.9]
        },
        "weight": mutator_child1_weight ∈ [0.1, 1.0]
      },
      {
        "type": "RandomSimpleMutator",
        "params": {
          "numMutations": mutator_child2_numMutations ∈ [1, 10],
          "p": mutator_child2_p ∈ [0.1, 0.9]
        },
        "weight": mutator_child2_weight ∈ [0.1, 1.0]
      }
    ]
  }
}
```

**Hyperparameters (7)**:
1. `mutator_comp_p`: Real [0.1, 1.0]
2. `mutator_child1_numMutations`: Integer [1, 10]
3. `mutator_child1_p`: Real [0.1, 0.9]
4. `mutator_child1_weight`: Real [0.1, 1.0]
5. `mutator_child2_numMutations`: Integer [1, 10]
6. `mutator_child2_p`: Real [0.1, 0.9]
7. `mutator_child2_weight`: Real [0.1, 1.0]

---

### CROSSOVER: CompositeCrossover (15 hyperparameters)

**ALL 5 base crossover types** included in one composite:

```json
{
  "type": "CompositeCrossover",
  "params": {
    "p": crossover_comp_p ∈ [0.1, 1.0],
    "children": [
      {
        "type": "GeometricColumnCrossover",
        "params": {
          "geoP": crossover_child1_geoP ∈ [0.1, 0.8],
          "crossoverProb": crossover_child1_crossoverProb ∈ [0.1, 0.95]
        },
        "weight": crossover_child1_weight ∈ [0.1, 1.0]
      },
      {
        "type": "GeometricRowCrossover",
        "params": {
          "geoP": crossover_child2_geoP ∈ [0.1, 0.8],
          "crossoverProb": crossover_child2_crossoverProb ∈ [0.1, 0.95]
        },
        "weight": crossover_child2_weight ∈ [0.1, 1.0]
      },
      {
        "type": "SinglePointCrossover",
        "params": {
          "p": crossover_child3_p ∈ [0.1, 0.9]
        },
        "weight": crossover_child3_weight ∈ [0.1, 1.0]
      },
      {
        "type": "KSwitchCrossover",
        "params": {
          "k": crossover_child4_k ∈ [2, 8],
          "p": crossover_child4_p ∈ [0.1, 0.9]
        },
        "weight": crossover_child4_weight ∈ [0.1, 1.0]
      },
      {
        "type": "ColumnKSwitchCrossover",
        "params": {
          "k": crossover_child5_k ∈ [2, 8],
          "p": crossover_child5_p ∈ [0.1, 0.9]
        },
        "weight": crossover_child5_weight ∈ [0.1, 1.0]
      }
    ]
  }
}
```

**Hyperparameters (15)**:
1. `crossover_comp_p`: Real [0.1, 1.0]
2. `crossover_child1_geoP`: Real [0.1, 0.8]
3. `crossover_child1_crossoverProb`: Real [0.1, 0.95]
4. `crossover_child1_weight`: Real [0.1, 1.0]
5. `crossover_child2_geoP`: Real [0.1, 0.8]
6. `crossover_child2_crossoverProb`: Real [0.1, 0.95]
7. `crossover_child2_weight`: Real [0.1, 1.0]
8. `crossover_child3_p`: Real [0.1, 0.9]
9. `crossover_child3_weight`: Real [0.1, 1.0]
10. `crossover_child4_k`: Integer [2, 8]
11. `crossover_child4_p`: Real [0.1, 0.9]
12. `crossover_child4_weight`: Real [0.1, 1.0]
13. `crossover_child5_k`: Integer [2, 8]
14. `crossover_child5_p`: Real [0.1, 0.9]
15. `crossover_child5_weight`: Real [0.1, 1.0]

---

### GENERATOR: Fixed AllSundaysHaveWorkGenerator (0 hyperparameters)

```json
{
  "type": "CompositeGenerator",
  "params": {
    "children": [
      {
        "type": "AllSundaysHaveWorkGenerator",
        "params": {},
        "weight": 1.0
      }
    ]
  }
}
```

**Note**: No hyperparameters needed. Only one generator type is available.

---

### SELECTION (2)
- `selection_type`: Categorical ["TournamentSelection", "RankSelection"]
- `selection_tournamentSize`: Integer [2, 6]

### FITNESS (1)
- `fitness_type`: Categorical ["FastIntersectUnionFitness", "CorrectFitness"]

### LOGGER (1)
- `logger_type`: Categorical ["SoutLogger"]

### Optional (1)
- `deterministic`: Categorical [True, False]

---

## Dimension Count

| Component | Hyperparameters | Total |
|-----------|-----------------|-------|
| General Settings | 2 | 2 |
| GA Base Parameters | 5 | 5 |
| Mutator | 7 | 7 |
| Crossover | 15 | 15 |
| Generator | 0 | 0 |
| Selection | 2 | 2 |
| Fitness | 1 | 1 |
| Logger | 1 | 1 |
| **Subtotal** | | **33** |
| Deterministic (optional) | 1 | 1 |
| **Total with deterministic** | | **34** |

---

## Key Design Decisions

✅ **ALL crossovers included**: GeometricColumn, GeometricRow, SinglePoint, KSwitch, ColumnKSwitch
- Each crossover has its own hyperparameters + weight
- Optimizer can learn best mixing weights for each type
- No explicit type choice needed; weights encode preference

✅ **Mutator with 2 RandomSimpleMutators**: 
- Only one mutator type available currently
- Both children use RandomSimpleMutator with independent hyperparameters
- Weights allow them to contribute differently

✅ **Generator fixed**: 
- Only AllSundaysHaveWorkGenerator available
- No choice or weight tuning needed
- Simplifies search space

---

## Example Generated Configuration

Sample from 33 dimensions:
```python
{
    "mutator_comp_p": 0.75,
    "mutator_child1_numMutations": 5,
    "mutator_child1_p": 0.4,
    "mutator_child1_weight": 0.6,
    "mutator_child2_numMutations": 3,
    "mutator_child2_p": 0.7,
    "mutator_child2_weight": 0.4,
    
    "crossover_comp_p": 0.85,
    "crossover_child1_geoP": 0.5,
    "crossover_child1_crossoverProb": 0.8,
    "crossover_child1_weight": 0.3,
    "crossover_child2_geoP": 0.6,
    "crossover_child2_crossoverProb": 0.7,
    "crossover_child2_weight": 0.2,
    "crossover_child3_p": 0.5,
    "crossover_child3_weight": 0.1,
    "crossover_child4_k": 4,
    "crossover_child4_p": 0.6,
    "crossover_child4_weight": 0.25,
    "crossover_child5_k": 3,
    "crossover_child5_p": 0.5,
    "crossover_child5_weight": 0.15,
}
```

Generates GA settings with:
- **CompositeMutator** with 2 RandomSimpleMutators (weights 0.6 and 0.4)
- **CompositeCrossover** with all 5 crossovers (weights: 0.3, 0.2, 0.1, 0.25, 0.15)
- **CompositeGenerator** with single AllSundaysHaveWorkGenerator

---

## Optimization Goal

The Bayesian optimizer will discover:
- **Best parameter values** for each crossover type (e.g., optimal geoP for GeometricColumnCrossover)
- **Optimal weight distribution** across all 5 crossovers
- **Best mutator parameter combinations** for the two children
- How these interact with GA base parameters (population, generations, etc.)

This allows automatic discovery of the best operator mix without pre-selecting which ones to use!

---

## Ready for Tuning

```bash
cd hyperparameter-optimization
python main.py
```

All 33 hyperparameters are active and will be optimized by the Bayesian optimizer! 🚀
