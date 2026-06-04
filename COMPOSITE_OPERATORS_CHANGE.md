# Search Space Change Summary

## What Changed

### Before
```
Mutator:
  Type = [RandomSimpleMutator | CompositeMutator]
  IF CompositeMutator THEN:
    - p (param)
    - child1: type + params + weight
    - child2: type + params + weight
  ELSE:
    - numMutations (param)
    - p (param)
    [child weights IGNORED]

Crossover:
  Type = [GeometricColumnCrossover | GeometricRowCrossover | ... | CompositeCrossover]
  IF CompositeCrossover THEN:
    - p (param)
    - child1: type + params + weight
    - child2: type + params + weight
  ELSE:
    - params specific to chosen type
    [child weights IGNORED]

Generator:
  Type = [AllSundaysHaveWorkGenerator | RandomGenerator | SeedingGenerator | CompositeGenerator]
  IF CompositeGenerator THEN:
    - child1: type + weight
    - child2: type + weight
  ELSE:
    [all child params IGNORED]
```

**Problem**: Wasted search space. Many dimensions are always ignored.

---

### After ✓
```
Mutator:
  ALWAYS CompositeMutator
  - p: 0.1-1.0 (hyperparameter)
  - child1:
      type: RandomSimpleMutator
      numMutations: 1-10
      p: 0.1-0.9
      weight: 0.1-1.0 ← HYPERPARAMETER
  - child2:
      type: RandomSimpleMutator
      numMutations: 1-10
      p: 0.1-0.9
      weight: 0.1-1.0 ← HYPERPARAMETER

Crossover:
  ALWAYS CompositeCrossover
  - p: 0.1-1.0 (hyperparameter)
  - child1:
      type: [5 base types]
      params: all tuned
      weight: 0.1-1.0 ← HYPERPARAMETER
  - child2:
      type: [5 base types]
      params: all tuned
      weight: 0.1-1.0 ← HYPERPARAMETER

Generator:
  ALWAYS CompositeGenerator
  - child1:
      type: [3 base types]
      weight: 0.1-1.0 ← HYPERPARAMETER
  - child2:
      type: [3 base types]
      weight: 0.1-1.0 ← HYPERPARAMETER
```

**Benefit**: Every dimension is always used. No wasted search space. Weights are actively tuned.

---

## How It Works with Hyperparameter Tuning

### Gaussian Process Perspective
- **48 dimensions** in continuous/categorical space
- **Every sample** is valid and produces a working configuration
- **No branching logic** that causes dimensions to be ignored
- **Weights as hyperparameters** mean the optimizer can:
  - Favor one child heavily (e.g., weight1=0.8, weight2=0.2)
  - Balance both children (e.g., weight1=0.5, weight2=0.5)
  - Essentially "select" which operators to use via weights

### Example: Optimizer Behavior
The Bayesian optimizer can discover patterns like:
- "High `mutator_child1_weight` correlates with good fitness"
- "When `crossover_child1_type=GeometricColumnCrossover`, low k works better for `crossover_child2_type=KSwitchCrossover`"
- "Balanced generator weights (0.5, 0.5) are better than skewed"

---

## Validation Checklist

✅ Search space removed type choices for mutator, crossover, generator
✅ Weights are now part of the search dimensions
✅ All child hyperparameters included in search space
✅ `build_search_space()` generates 48 dimensions (+ optional deterministic)
✅ `build_ga_settings()` unconditionally creates CompositeMutator/CompositeCrossover/CompositeGenerator
✅ Each child gets its `type`, `params`, and `weight` from sample
✅ `build_settings_payload()` works for all samples (no branching issues)
✅ Generated GA settings JSON has proper composite structure for Java backend
✅ Works with main.py's optimizer and materialization flow

---

## Example Run-Through

1. **Optimizer samples 48 dimensions**:
   ```
   [7.5, 15.0, 150, 3000, ..., 'RandomSimpleMutator', 5, 0.5, 0.7, ...]
   ```

2. **`build_settings_payload(sample)` processes it**:
   - Reads `mutator_comp_p=0.8`
   - Builds CompositeMutator with:
     - child1: RandomSimpleMutator + weight 0.7
     - child2: RandomSimpleMutator + weight 0.3

3. **API receives properly structured GA settings**:
   ```json
   {
     "mutator": {
       "type": "CompositeMutator",
       "params": {
         "p": 0.8,
         "children": [
           {"type": "RandomSimpleMutator", "params": {...}, "weight": 0.7},
           {"type": "RandomSimpleMutator", "params": {...}, "weight": 0.3}
         ]
       }
     }
   }
   ```

4. **Java backend instantiates**:
   ```java
   new CompositeMutator(
     0.8,
     List.of(mutator1, mutator2),
     new double[]{0.7, 0.3}
   )
   ```

5. **Optimization runs and returns fitness score**

6. **Optimizer learns patterns and suggests better samples**

---

## Files Modified

- **[search_space.py](hyperparameter-optimization/search_space.py)**
  - Removed `MUTATOR_TYPES`, `CROSSOVER_TYPES`, `GENERATOR_TYPES` constants
  - Updated `build_search_space()` to remove type choices
  - Simplified `build_ga_settings()` to always use composite
  - Kept `build_mutator_child()`, `build_crossover_child()`, `build_generator_child()` helper functions

## Files NOT Modified (No Breaking Changes)

- **main.py** - Works as-is with new search space
- **api_client.py** - Sends GA settings to API unchanged
- **Backend API** - Already handles composite operators
- **Java algorithm** - Already implements composite operators

---

## Ready for Hyperparameter Tuning! 🚀

This change ensures that hyperparameter tuning can effectively explore:
- Different operator weights
- Balanced vs. specialized operator combinations
- Trade-offs in composite operator mixing

All within a clean, wasted-space-free 48-dimensional search space.
