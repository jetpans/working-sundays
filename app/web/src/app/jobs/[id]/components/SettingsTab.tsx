"use client";

import { useEffect, useMemo, useState } from "react";
import { useApiFetch } from "@/hooks/useApiFetch";
import { toast } from "sonner";

interface SettingsTabProps {
  username: string;
  jobId: string;
  server: string;
  initialDescriptor?: any;
  onValidationChange?: (valid: boolean) => void;
  onSaved?: (payload: { general: any; ga: any }) => void;
}

// Operator type lists (kept in sync with Java classes)
const MUTATORS = ["RandomSimpleMutator", "CompositeMutator"];
const CROSSOVERS = [
  "GeometricColumnCrossover",
  "GeometricRowCrossover",
  "SinglePointCrossover",
  "KSwitchCrossover",
  "ColumnKSwitchCrossover",
  "CompositeCrossover",
];
const SELECTIONS = ["TournamentSelection", "RankSelection"];
const ELIMINATORS = ["EliteEliminator", "EliteGeometricEliminator"];
const FITNESSES = ["FastIntersectUnionFitness", "CorrectFitness"];
const GENERATORS = [
  "AllSundaysHaveWorkGenerator",
  "CompositeGenerator",
  "ForStoresGenerator",
  "RandomGenerator",
  "SeedingGenerator",
];
const LOGGERS = ["SoutLogger"];

function numberInput(props: any) {
  return (
    <input
      type="number"
      step={props.step || "0.1"}
      value={props.value}
      onChange={(e) => props.onChange(Number(e.target.value))}
      className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
    />
  );
}

function TextInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
    />
  );
}

// Render parameter editors for known operator types. If a type has no parameters, return null.
function OperatorParamsEditor({
  type,
  value,
  onChange,
  inComposite,
}: {
  type: string;
  value: any;
  onChange: (v: any) => void;
  inComposite?: boolean;
}) {
  if (!type) return null;

  // Mutators
  if (type === "RandomSimpleMutator") {
    return (
      <div className="space-y-2">
        <label className="text-sm text-slate-600">numMutations</label>
        {numberInput({
          value: value?.numMutations ?? 5,
          onChange: (v: number) => onChange({ ...value, numMutations: v }),
          step: 1,
        })}
        <label className="text-sm text-slate-600">p</label>
        {numberInput({
          value: value?.p ?? 0.5,
          onChange: (v: number) => onChange({ ...value, p: v }),
          step: 0.01,
        })}
      </div>
    );
  }

  if (type === "CompositeMutator") {
    // composite: p, weights (comma), children
    return (
      <div className="space-y-2">
        <label className="text-sm text-slate-600">p</label>
        {numberInput({
          value: value?.p ?? 1,
          onChange: (v: number) => onChange({ ...value, p: v }),
        })}
        <div className="text-sm text-slate-500">
          Weights are set per child below (default 1.0)
        </div>
        <div>
          <label className="text-sm text-slate-600">Children</label>
          <CompositeChildrenEditor
            items={value?.children || []}
            onChange={(children) => onChange({ ...value, children })}
            family="mutator"
          />
        </div>
      </div>
    );
  }

  // Crossovers
  if (type === "GeometricColumnCrossover" || type === "GeometricRowCrossover") {
    return (
      <div className="space-y-2">
        <label className="text-sm text-slate-600">geoP</label>
        {numberInput({
          value: value?.geoP ?? 0.3,
          onChange: (v: number) => onChange({ ...value, geoP: v }),
          step: 0.01,
        })}
        <label className="text-sm text-slate-600">crossoverProb</label>
        {numberInput({
          value: value?.crossoverProb ?? 0.7,
          onChange: (v: number) => onChange({ ...value, crossoverProb: v }),
          step: 0.01,
        })}
      </div>
    );
  }

  if (type === "SinglePointCrossover") {
    return (
      <div>
        <label className="text-sm text-slate-600">p</label>
        {numberInput({
          value: value?.p ?? 0.5,
          onChange: (v: number) => onChange({ ...value, p: v }),
          step: 0.01,
        })}
      </div>
    );
  }

  if (type === "KSwitchCrossover" || type === "ColumnKSwitchCrossover") {
    return (
      <div className="space-y-2">
        <label className="text-sm text-slate-600">k</label>
        {numberInput({
          value: value?.k ?? 3,
          onChange: (v: number) => onChange({ ...value, k: v }),
          step: 1,
        })}
        <label className="text-sm text-slate-600">p</label>
        {numberInput({
          value: value?.p ?? 0.5,
          onChange: (v: number) => onChange({ ...value, p: v }),
          step: 0.01,
        })}
      </div>
    );
  }

  if (type === "CompositeCrossover") {
    return (
      <div className="space-y-2">
        <label className="text-sm text-slate-600">p</label>
        {numberInput({
          value: value?.p ?? 1,
          onChange: (v: number) => onChange({ ...value, p: v }),
        })}
        <div className="text-sm text-slate-500">
          Weights are set per child below (default 1.0)
        </div>
        <div>
          <label className="text-sm text-slate-600">Children</label>
          <CompositeChildrenEditor
            items={value?.children || []}
            onChange={(children) => onChange({ ...value, children })}
            family="crossover"
          />
        </div>
      </div>
    );
  }

  // Selection
  if (type === "TournamentSelection") {
    return (
      <div>
        <label className="text-sm text-slate-600">tournamentSize</label>
        {numberInput({
          value: value?.tournamentSize ?? 3,
          onChange: (v: number) => onChange({ ...value, tournamentSize: v }),
          step: 1,
        })}
      </div>
    );
  }

  if (type === "EliteEliminator") {
    return (
      <div>
        <label className="text-sm text-slate-600">elitism</label>
        {numberInput({
          value: value?.elitism ?? 5,
          onChange: (v: number) => onChange({ ...value, elitism: v }),
          step: 1,
        })}
      </div>
    );
  }

  if (type === "EliteGeometricEliminator") {
    return (
      <div className="space-y-2">
        <div>
          <label className="text-sm text-slate-600">survivalRate</label>
          {numberInput({
            value: value?.survivalRate ?? 0.2,
            onChange: (v: number) => onChange({ ...value, survivalRate: v }),
            step: 0.01,
          })}
        </div>
        <div>
          <label className="text-sm text-slate-600">p</label>
          {numberInput({
            value: value?.p ?? 0.5,
            onChange: (v: number) => onChange({ ...value, p: v }),
            step: 0.01,
          })}
        </div>
      </div>
    );
  }

  // RankSelection and fitnesses/generators/loggers with no params
  if (
    type === "RankSelection" ||
    type === "FastIntersectUnionFitness" ||
    type === "CorrectFitness" ||
    type === "RandomGenerator" ||
    type === "SeedingGenerator" ||
    type === "AllSundaysHaveWorkGenerator" ||
    type === "ForStoresGenerator" ||
    type === "SoutLogger"
  ) {
    // Some generators accept store list in constructor (ForStoresGenerator) - skip complex class refs here
    return (
      <div className="text-sm text-slate-500">No additional parameters</div>
    );
  }

  if (type === "CompositeGenerator") {
    return (
      <div className="space-y-2">
        <div className="text-sm text-slate-500">
          Weights are set per child below (default 1.0)
        </div>
        <div>
          <label className="text-sm text-slate-600">Children</label>
          <CompositeChildrenEditor
            items={value?.children || []}
            onChange={(children) => onChange({ ...value, children })}
            family="generator"
          />
        </div>
      </div>
    );
  }

  return null;
}

function CompositeChildrenEditor({
  items,
  onChange,
  family,
}: {
  items: any[];
  onChange: (v: any[]) => void;
  family: string;
}) {
  const add = () =>
    onChange([...(items || []), { type: "", params: {}, weight: 1.0 }]);
  const removeAt = (i: number) => onChange(items.filter((_, idx) => idx !== i));
  const updateAt = (i: number, v: any) =>
    onChange(items.map((it, idx) => (idx === i ? v : it)));

  // family controls available types and hides composite variants inside children
  const familyTypes = (family: string) => {
    if (family === "mutator")
      return MUTATORS.filter((t) => !t.startsWith("Composite"));
    if (family === "crossover")
      return CROSSOVERS.filter((t) => !t.startsWith("Composite"));
    if (family === "generator")
      return GENERATORS.filter((t) => !t.startsWith("Composite"));
    return [];
  };

  return (
    <div className="space-y-2">
      <div className="bg-slate-50 border border-slate-100 rounded p-3">
        <div className="mb-2 text-sm font-medium text-slate-700">
          Composite Children
        </div>
        {(items || []).map((it, idx) => (
          <div key={idx} className="border rounded p-2 mb-2 bg-white">
            <div className="flex gap-2 items-center">
              <select
                value={it.type || ""}
                onChange={(e) =>
                  updateAt(idx, {
                    ...it,
                    type: e.target.value,
                    params: it.params || {},
                    weight: it.weight ?? 1.0,
                  })
                }
                className="flex-1 rounded border border-slate-200 px-2 py-1 text-sm"
              >
                <option value="">-- choose --</option>
                {familyTypes(family).map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>

              <div className="w-28">
                <label className="block text-xs text-slate-500">Weight</label>
                <input
                  type="number"
                  step="0.1"
                  value={it.weight ?? 1.0}
                  onChange={(e) =>
                    updateAt(idx, { ...it, weight: Number(e.target.value) })
                  }
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1 text-sm"
                />
              </div>

              <button
                onClick={() => removeAt(idx)}
                className="text-sm text-red-500"
              >
                Remove
              </button>
            </div>
            <div className="mt-2">
              <OperatorParamsEditor
                type={it.type}
                value={it.params || {}}
                onChange={(p: any) => updateAt(idx, { ...it, params: p })}
                inComposite={true}
              />
            </div>
          </div>
        ))}

        <div className="pt-2">
          <button onClick={add} className="text-sm text-blue-600">
            + Add child to composite
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SettingsTab({
  username,
  jobId,
  server,
  initialDescriptor,
  onValidationChange,
  onSaved,
}: SettingsTabProps) {
  const apiFetch = useApiFetch();
  // defaults
  const defaults = useMemo(
    () => ({
      general: {
        MAX_CLUSTER_DISTANCE: 3,
        MAX_CLUSTER_JOIN_DISTANCE: 10,
      },
      ga: {
        populationSize: 100,
        generations: 5000,
        newChromosomes: 2,
        numThreads: 4,
        deterministic: true,
        timelimit: 3600,
        stagnationFraction: 0.2,
        eliminator: {
          type: "EliteEliminator",
          params: { elitism: 5 },
        },
        mutator: {
          type: "CompositeMutator",
          params: { p: 1, weights: [1], children: [] },
        },
        crossover: {
          type: "CompositeCrossover",
          params: { p: 1, weights: [0.4, 0.4, 0.2], children: [] },
        },
        selection: {
          type: "TournamentSelection",
          params: { tournamentSize: 3 },
        },
        fitness: { type: "FastIntersectUnionFitness", params: {} },
        generator: { type: "AllSundaysHaveWorkGenerator", params: {} },
        logger: { type: "SoutLogger", params: {} },
      },
    }),
    [],
  );

  const [general, setGeneral] = useState<any>(defaults.general);
  const [ga, setGa] = useState<any>(defaults.ga);
  const [saving, setSaving] = useState(false);

  const isValid = useMemo(() => {
    return (
      general.MAX_CLUSTER_DISTANCE !== undefined &&
      general.MAX_CLUSTER_JOIN_DISTANCE !== undefined &&
      ga.populationSize !== undefined &&
      ga.generations !== undefined &&
      ga.newChromosomes !== undefined &&
      ga.numThreads !== undefined &&
      ga.deterministic !== undefined &&
      ga.timelimit !== undefined &&
      ga.stagnationFraction !== undefined &&
      !!ga.eliminator?.type &&
      !!ga.mutator?.type &&
      !!ga.crossover?.type &&
      !!ga.selection?.type &&
      !!ga.fitness?.type &&
      !!ga.generator?.type &&
      !!ga.logger?.type
    );
  }, [general, ga]);

  useEffect(() => {
    if (!initialDescriptor) return;
    const s = initialDescriptor.settings || {};
    if (s.general) setGeneral((prev: any) => ({ ...prev, ...s.general }));
    if (s.ga) setGa((prev: any) => ({ ...prev, ...s.ga }));
  }, [initialDescriptor]);

  useEffect(() => {
    onValidationChange?.(isValid);
  }, [isValid, onValidationChange]);

  const save = async () => {
    setSaving(true);
    try {
      const res = await apiFetch(`/api/job/${username}/${jobId}/settings`, {
        method: "POST",
        body: JSON.stringify({ settings: { general, ga } }),
      });
      if (!res.ok) throw new Error(`Failed to save settings (${res.status})`);
      const data = await res.json();
      if (!data?.success) {
        throw new Error(data?.error || "Failed to save settings");
      }
      onValidationChange?.(true);
      onSaved?.({ general, ga });
      toast.success("Settings saved");
    } catch (e) {
      onValidationChange?.(false);
      toast.error(e instanceof Error ? e.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid grid-cols-2 gap-6">
      <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">General</h2>
        <div className="space-y-4">
          <div>
            <label
              title="Distance threshold for cluster radius calculation (km)"
              className="block text-sm font-medium text-slate-600"
            >
              Max Cluster Distance (km)
            </label>
            {numberInput({
              value: general.MAX_CLUSTER_DISTANCE,
              onChange: (v: number) =>
                setGeneral({ ...general, MAX_CLUSTER_DISTANCE: v }),
            })}
          </div>
          <div>
            <label
              title="Max distance between clusters to allow joining (km)"
              className="block text-sm font-medium text-slate-600"
            >
              Max Cluster Join Distance (km)
            </label>
            {numberInput({
              value: general.MAX_CLUSTER_JOIN_DISTANCE,
              onChange: (v: number) =>
                setGeneral({ ...general, MAX_CLUSTER_JOIN_DISTANCE: v }),
            })}
          </div>
        </div>
      </div>

      <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Genetic Algorithm (Advanced)</h2>

        <div className="space-y-3">
          <div>
            <label
              title="Number of individuals in the GA population"
              className="block text-sm font-medium text-slate-600"
            >
              Population Size
            </label>
            {numberInput({
              value: ga.populationSize,
              onChange: (v: number) => setGa({ ...ga, populationSize: v }),
              step: 1,
            })}
          </div>
          <div>
            <label
              title="How many generations the GA will run"
              className="block text-sm font-medium text-slate-600"
            >
              Generations
            </label>
            {numberInput({
              value: ga.generations,
              onChange: (v: number) => setGa({ ...ga, generations: v }),
              step: 1,
            })}
          </div>
          <div>
            <label
              title="Number of newly generated chromosomes per generation"
              className="block text-sm font-medium text-slate-600"
            >
              New Chromosomes
            </label>
            {numberInput({
              value: ga.newChromosomes,
              onChange: (v: number) => setGa({ ...ga, newChromosomes: v }),
              step: 1,
            })}
          </div>
          <div>
            <label
              title="Number of worker threads for multi-threaded runs"
              className="block text-sm font-medium text-slate-600"
            >
              Num Threads
            </label>
            {numberInput({
              value: ga.numThreads,
              onChange: (v: number) => setGa({ ...ga, numThreads: v }),
              step: 1,
            })}
          </div>

          <div className="flex items-center gap-2">
            <input
              id="ga-deterministic"
              type="checkbox"
              checked={Boolean(ga.deterministic)}
              onChange={(e) =>
                setGa({ ...ga, deterministic: e.target.checked })
              }
              className="h-4 w-4 rounded border-slate-300 text-slate-900"
            />
            <label
              htmlFor="ga-deterministic"
              className="text-sm font-medium text-slate-600"
              title="Use a fixed PRNG seed for reproducible runs"
            >
              Deterministic
            </label>
          </div>

          <div>
            <label
              title="Maximum time (seconds) the GA can run before stopping gracefully"
              className="block text-sm font-medium text-slate-600"
            >
              Time Limit (seconds)
            </label>
            {numberInput({
              value: ga.timelimit,
              onChange: (v: number) => setGa({ ...ga, timelimit: v }),
              step: 1,
            })}
          </div>

          <div>
            <label
              title="Stop if no improvement for this fraction of generations (e.g., 0.2 = 20% of total generations)"
              className="block text-sm font-medium text-slate-600"
            >
              Stagnation Fraction
            </label>
            {numberInput({
              value: ga.stagnationFraction,
              onChange: (v: number) => setGa({ ...ga, stagnationFraction: v }),
              step: 0.01,
            })}
            <p className="text-xs text-slate-500 mt-1">
              Stop if no improvement for ~
              {Math.floor(
                (ga.stagnationFraction || 0.2) * (ga.generations || 5000),
              )}{" "}
              generations
            </p>
          </div>

          {/* Operators */}
          <div>
            <label
              title="Mutation operator: alters chromosomes randomly"
              className="block text-sm font-medium text-slate-600"
            >
              Mutator
            </label>
            <OperatorSelector
              family="mutator"
              type={ga.mutator?.type}
              params={ga.mutator?.params}
              onChange={(t, p) =>
                setGa({ ...ga, mutator: { type: t, params: p } })
              }
            />
          </div>

          <div>
            <label
              title="Crossover operator: combines parents to produce children"
              className="block text-sm font-medium text-slate-600"
            >
              Crossover
            </label>
            <OperatorSelector
              family="crossover"
              type={ga.crossover?.type}
              params={ga.crossover?.params}
              onChange={(t, p) =>
                setGa({ ...ga, crossover: { type: t, params: p } })
              }
            />
          </div>

          <div>
            <label
              title="Selection strategy: chooses parents from population"
              className="block text-sm font-medium text-slate-600"
            >
              Selection
            </label>
            <OperatorSelector
              family="selection"
              type={ga.selection?.type}
              params={ga.selection?.params}
              onChange={(t, p) =>
                setGa({ ...ga, selection: { type: t, params: p } })
              }
            />
          </div>

          <div>
            <label
              title="Elimination strategy: chooses survivors after evaluation"
              className="block text-sm font-medium text-slate-600"
            >
              Eliminator
            </label>
            <OperatorSelector
              family="eliminator"
              type={ga.eliminator?.type}
              params={ga.eliminator?.params}
              onChange={(t, p) =>
                setGa({ ...ga, eliminator: { type: t, params: p } })
              }
            />
          </div>

          <div>
            <label
              title="Fitness function: evaluates chromosome quality"
              className="block text-sm font-medium text-slate-600"
            >
              Fitness
            </label>
            <OperatorSelector
              family="fitness"
              type={ga.fitness?.type}
              params={ga.fitness?.params}
              onChange={(t, p) =>
                setGa({ ...ga, fitness: { type: t, params: p } })
              }
            />
          </div>

          <div>
            <label
              title="Generator: produces initial chromosomes / seeding"
              className="block text-sm font-medium text-slate-600"
            >
              Generator
            </label>
            <OperatorSelector
              family="generator"
              type={ga.generator?.type}
              params={ga.generator?.params}
              onChange={(t, p) =>
                setGa({ ...ga, generator: { type: t, params: p } })
              }
            />
          </div>

          <div>
            <label
              title="Logger: controls algorithm output logging"
              className="block text-sm font-medium text-slate-600"
            >
              Logger
            </label>
            <OperatorSelector
              family="logger"
              type={ga.logger?.type}
              params={ga.logger?.params}
              onChange={(t, p) =>
                setGa({ ...ga, logger: { type: t, params: p } })
              }
            />
          </div>

          <div className="flex gap-2 mt-4">
            <button
              onClick={save}
              disabled={saving}
              className="rounded bg-slate-900 px-4 py-2 text-white"
            >
              {saving ? "Saving..." : "Save Settings"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function OperatorSelector({
  family,
  type,
  params,
  onChange,
}: {
  family: string;
  type: string;
  params: any;
  onChange: (t: string, p: any) => void;
}) {
  const types = useMemo(() => {
    if (family === "mutator") return MUTATORS;
    if (family === "crossover") return CROSSOVERS;
    if (family === "selection") return SELECTIONS;
    if (family === "eliminator") return ELIMINATORS;
    if (family === "fitness") return FITNESSES;
    if (family === "generator") return GENERATORS;
    if (family === "logger") return LOGGERS;
    return [];
  }, [family]);

  const onTypeChange = (t: string) => {
    // hide composite choices when in composite children handled elsewhere
    onChange(t, {});
  };

  return (
    <div className="space-y-2">
      <select
        value={type || ""}
        onChange={(e) => onTypeChange(e.target.value)}
        className="w-full rounded border border-slate-200 px-2 py-1 text-sm"
      >
        <option value="">-- choose --</option>
        {types.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
      <div>
        {OperatorParamsEditor({
          type: type || "",
          value: params,
          onChange: (p: any) => onChange(type, p),
        })}
      </div>
    </div>
  );
}
