"use client";

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { toast } from "sonner";
import { useApiFetch } from "@/hooks/useApiFetch";
import {
  Store,
  StoreConstraints,
  calculateSundaysInYear,
  validateStoreData,
  validateConstraints,
} from "@/lib/jobUtils";
import StoreMap from "./StoreMap";
import StoreList from "./StoreList";
import ConstraintsEditorModal from "./ConstraintsEditorModal";

interface StoresTabProps {
  username: string;
  jobId: string;
  server: string;
  initialStores?: Record<string, Store> | null;
  initialConstraints?: Record<string, StoreConstraints> | null;
  initialRadiusCalc?: string | null;
  initialGeneralSettings?: Record<string, any> | null;
  initialSettings?: Record<string, any> | null;
  onImportedJob?: (payload: {
    stores?: Record<string, Store>;
    constraints?: Record<string, any>;
    radiusCalc?: string;
    settings?: Record<string, any>;
  }) => void;
  onValidationChange?: (valid: boolean) => void;
  onDirtyChange?: (dirty: boolean) => void;
}

export default function StoresTab({
  username,
  jobId,
  server,
  initialStores,
  initialConstraints,
  initialRadiusCalc,
  initialGeneralSettings,
  initialSettings,
  onImportedJob,
  onValidationChange,
  onDirtyChange,
}: StoresTabProps) {
  const apiFetch = useApiFetch();
  const [stores, setStores] = useState<Record<string, Store>>({});
  // clustering removed — algorithm-java handles clustering
  const [globalConstraints, setGlobalConstraints] = useState<any>({});
  const [constraintsMap, setConstraintsMap] = useState<
    Record<string, StoreConstraints>
  >({});
  const [radiusCalculator, setRadiusCalculator] = useState<string>(
    "return store.get('user_ratings_total', 5) * 1",
  );
  const [generalSettings, setGeneralSettings] = useState<any>({
    MAX_THEORETICAL_RADIUS_KM: 5.0,
    MIN_RADIUS_KM: 0.5,
    COMPETITION_SENSITIVITY: 0.08,
    MAX_CLUSTER_DISTANCE: 3,
    MAX_CLUSTER_JOIN_DISTANCE: 10,
  });
  const [settingsForSave, setSettingsForSave] = useState<Record<string, any>>(
    {},
  );
  const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);
  const [sundays, setSundays] = useState<Date[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isPersisted, setIsPersisted] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const importInputRef = useRef<HTMLInputElement | null>(null);
  const hasHydratedServerState = useRef(false);

  const markDirty = useCallback(() => {
    setIsDirty(true);
    setIsPersisted(false);
  }, []);

  const applyConstraints = useCallback((constraints: Record<string, any>) => {
    const gc = { ...constraints };
    const globalOnly: any = {
      YEAR: gc.YEAR,
      SUNDAYS: gc.SUNDAYS,
      MAX_WORKS: gc.MAX_WORKS,
      MAX_DOESNT_WORK: gc.MAX_DOESNT_WORK,
    };
    setGlobalConstraints(globalOnly);

    const perStore: Record<string, StoreConstraints> = {};
    Object.keys(gc).forEach((k) => {
      if (!["YEAR", "SUNDAYS", "MAX_WORKS", "MAX_DOESNT_WORK"].includes(k)) {
        perStore[k] = gc[k] as StoreConstraints;
      }
    });
    setConstraintsMap(perStore);
  }, []);

  // Load initial data from server if provided
  useEffect(() => {
    if (hasHydratedServerState.current) return;

    const hasServerStores =
      initialStores !== undefined && initialStores !== null;
    const hasServerConstraints =
      initialConstraints !== undefined && initialConstraints !== null;
    const hasServerRadiusCalc =
      initialRadiusCalc !== undefined && initialRadiusCalc !== null;
    const hasServerGeneralSettings =
      initialGeneralSettings !== undefined && initialGeneralSettings !== null;
    const hasServerSettings =
      initialSettings !== undefined && initialSettings !== null;

    if (
      !hasServerStores &&
      !hasServerConstraints &&
      !hasServerRadiusCalc &&
      !hasServerGeneralSettings &&
      !hasServerSettings
    ) {
      return;
    }

    setStores(initialStores || {});
    if (initialConstraints) applyConstraints(initialConstraints);
    if (initialRadiusCalc) setRadiusCalculator(initialRadiusCalc);
    if (initialGeneralSettings) {
      setGeneralSettings((prev: any) => ({
        ...prev,
        ...initialGeneralSettings,
      }));
    }
    if (initialSettings) setSettingsForSave(initialSettings);

    const hasSavedStores =
      !!initialStores && Object.keys(initialStores).length > 0;
    const hasSavedConstraints =
      !!initialConstraints &&
      typeof (initialConstraints as any).YEAR !== "undefined" &&
      typeof (initialConstraints as any).SUNDAYS !== "undefined" &&
      typeof (initialConstraints as any).MAX_WORKS !== "undefined" &&
      typeof (initialConstraints as any).MAX_DOESNT_WORK !== "undefined";
    const hasSavedRadiusCalc =
      !!initialRadiusCalc && initialRadiusCalc.trim().length > 0;

    setIsPersisted(hasSavedStores && hasSavedConstraints && hasSavedRadiusCalc);
    setIsDirty(false);

    hasHydratedServerState.current = true;
  }, [
    initialStores,
    initialConstraints,
    initialRadiusCalc,
    initialGeneralSettings,
    initialSettings,
    applyConstraints,
  ]);

  // Recompute sundays when YEAR changes
  useEffect(() => {
    const y = Number(globalConstraints.YEAR);
    if (y && !isNaN(y)) setSundays(calculateSundaysInYear(y));
    else setSundays([]);
  }, [globalConstraints.YEAR]);

  const storeIds = useMemo(() => Object.keys(stores), [stores]);

  const handleDataFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const parsed = JSON.parse(String(reader.result || "{}"));
          const validation = validateStoreData(parsed);
          if (!validation.valid) {
            toast.error(`Invalid store data: ${validation.errors.join("; ")}`);
            return;
          }
          setStores(parsed);
          markDirty();
          toast.success("Stores file loaded");
        } catch (err) {
          toast.error("Failed to parse stores JSON file");
        }
      };
      reader.readAsText(f);
    },
    [markDirty],
  );

  // clustering upload removed

  const handleDeleteStore = useCallback(
    (storeId: string) => {
      setStores((prev) => {
        const n = { ...prev };
        delete n[storeId];
        return n;
      });
      setConstraintsMap((prev) => {
        const n = { ...prev };
        delete n[storeId];
        return n;
      });
      markDirty();
      toast.success("Store deleted");
    },
    [markDirty],
  );

  const handleStoreSelect = useCallback((storeId: string) => {
    setSelectedStoreId(storeId);
  }, []);

  const handleConstraintsSave = useCallback(
    (storeId: string, constraints: StoreConstraints) => {
      setConstraintsMap((prev) => ({ ...prev, [storeId]: constraints }));
      markDirty();
      setSelectedStoreId(null);
      toast.success("Constraints saved");
    },
    [markDirty],
  );

  const isValid = useMemo(() => {
    const hasStores = storeIds.length > 0;
    const hasGlobalConstraints =
      globalConstraints.YEAR &&
      globalConstraints.SUNDAYS &&
      globalConstraints.MAX_WORKS !== undefined;
    const hasRadiusCalc = radiusCalculator.trim().length > 0;

    return hasStores && hasGlobalConstraints && hasRadiusCalc;
  }, [storeIds, globalConstraints, radiusCalculator]);

  useEffect(() => {
    onValidationChange?.(isValid && isPersisted);
  }, [isValid, isPersisted, onValidationChange]);

  useEffect(() => {
    onDirtyChange?.(isDirty);
  }, [isDirty, onDirtyChange]);

  const handleSave = async () => {
    if (!isValid) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      setIsSaving(true);

      const settingsResponse = await apiFetch(
        `/api/job/${username}/${jobId}/settings`,
        {
          method: "POST",
          body: JSON.stringify({
            settings: { ...settingsForSave, general: generalSettings },
          }),
        },
      );
      if (!settingsResponse.ok) {
        throw new Error("Failed to save settings");
      }

      // Build constraints object merging global and per-store
      const fullConstraints: any = {
        YEAR: Number(globalConstraints.YEAR),
        SUNDAYS: Number(globalConstraints.SUNDAYS),
        MAX_WORKS: Number(globalConstraints.MAX_WORKS),
        MAX_DOESNT_WORK: Number(globalConstraints.MAX_DOESNT_WORK),
      };
      // add per-store entries
      Object.entries(constraintsMap).forEach(([id, c]) => {
        fullConstraints[id] = c;
      });

      const constraintsValidation = validateConstraints(
        fullConstraints,
        storeIds,
      );
      if (!constraintsValidation.valid) {
        toast.error(
          `Constraints validation failed: ${constraintsValidation.errors.join(", ")}`,
        );
        setIsSaving(false);
        return;
      }

      // Save stores (compute radius_km before writing)
      const storesResponse = await apiFetch(
        `/api/job/${username}/${jobId}/stores-with-radius`,
        {
          method: "POST",
          body: JSON.stringify({ stores, radius_calc: radiusCalculator }),
        },
      );
      if (!storesResponse.ok) {
        let message = `Failed to save stores (${storesResponse.status})`;
        try {
          const body = await storesResponse.json();
          if (body?.error) message = body.error;
        } catch {
          // ignore
        }
        throw new Error(message);
      }

      // Save constraints
      const constraintsResponse = await apiFetch(
        `/api/job/${username}/${jobId}/constraints`,
        {
          method: "POST",
          body: JSON.stringify({ constraints: fullConstraints }),
        },
      );
      if (!constraintsResponse.ok)
        throw new Error(
          `Failed to save constraints (${constraintsResponse.status})`,
        );

      setIsPersisted(true);
      setIsDirty(false);

      toast.success("Stores tab saved successfully");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to save stores tab",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const res = await apiFetch(`/api/job/${username}/${jobId}/export`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(`Failed to export job (${res.status})`);
      const body = await res.json();
      if (!body.success) throw new Error(body.error || "Failed to export job");

      const descriptor = body.data || {};
      const blob = new Blob([JSON.stringify(descriptor, null, 2)], {
        type: "application/octet-stream",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${jobId}.job`;
      a.click();
      URL.revokeObjectURL(url);

      toast.success("Job exported");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to export job",
      );
    } finally {
      setIsExporting(false);
    }
  };

  const handleImportClick = () => {
    importInputRef.current?.click();
  };

  const handleImportFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result || "{}"));
        if (!parsed || typeof parsed !== "object") {
          toast.error("Invalid job file format");
          return;
        }
        const importedStores = parsed.data as Record<string, Store> | undefined;
        const importedConstraints = parsed.constraints as
          | Record<string, any>
          | undefined;
        const importedSettings =
          parsed.settings && typeof parsed.settings === "object"
            ? (parsed.settings as Record<string, any>)
            : undefined;
        const importedRadiusCalc =
          parsed.value_for_radius_calculator || parsed.radius_calc;

        if (importedStores) {
          const validation = validateStoreData(parsed.data);
          if (!validation.valid) {
            toast.error(`Invalid store data: ${validation.errors.join("; ")}`);
            return;
          }
          setStores(importedStores);
        }
        // ignore clustering from imported job (algorithm will compute it)
        if (importedConstraints) applyConstraints(importedConstraints);
        if (importedRadiusCalc) {
          setRadiusCalculator(importedRadiusCalc);
        }
        if (importedSettings?.general) {
          setGeneralSettings((prev: any) => ({
            ...prev,
            ...importedSettings.general,
          }));
        }
        if (importedSettings) setSettingsForSave(importedSettings);
        onImportedJob?.({
          stores: importedStores,
          constraints: importedConstraints,
          radiusCalc: importedRadiusCalc,
          settings: importedSettings,
        });
        const hasImportedStores =
          !!importedStores && Object.keys(importedStores).length > 0;
        const hasImportedConstraints =
          !!importedConstraints &&
          importedConstraints.YEAR !== undefined &&
          importedConstraints.SUNDAYS !== undefined &&
          importedConstraints.MAX_WORKS !== undefined &&
          importedConstraints.MAX_DOESNT_WORK !== undefined;
        const hasImportedRadiusCalc =
          typeof importedRadiusCalc === "string" &&
          importedRadiusCalc.trim().length > 0;

        setIsPersisted(
          hasImportedStores && hasImportedConstraints && hasImportedRadiusCalc,
        );
        setIsDirty(false);
        toast.success("Job imported");
      } catch (err) {
        toast.error("Failed to parse job file");
      } finally {
        if (importInputRef.current) importInputRef.current.value = "";
      }
    };
    reader.readAsText(f);
  };

  return (
    <div className="space-y-4">
      <div className="md:flex md:gap-6">
        <div className="md:w-2/5">
          {/* Header with Save Button */}
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Stores Configuration</h2>
            <div className="flex items-center gap-2">
              <input
                ref={importInputRef}
                type="file"
                accept=".job"
                onChange={handleImportFile}
                className="hidden"
              />
              <button
                onClick={handleImportClick}
                className="rounded border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                Import Job
              </button>
              <button
                onClick={handleExport}
                disabled={isExporting}
                className="rounded border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
              >
                {isExporting ? "Exporting..." : "Export Job"}
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving || !isValid}
                className="rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
              >
                {isSaving ? "Saving..." : "Save Stores"}
              </button>
            </div>
          </div>

          {/* Global Constraints */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm mt-4">
            <h3 className="mb-4 font-semibold">Global Constraints</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  className="block text-sm font-medium text-slate-600"
                  title="Year used to calculate Sundays"
                >
                  Year
                </label>
                <input
                  type="number"
                  value={globalConstraints.YEAR || ""}
                  onChange={(e) => {
                    const y = parseInt(e.target.value);
                    setGlobalConstraints((prev: any) => ({
                      ...prev,
                      YEAR: y,
                      SUNDAYS: isNaN(y)
                        ? undefined
                        : calculateSundaysInYear(y).length,
                    }));
                    markDirty();
                  }}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1 text-sm"
                />
              </div>

              <div>
                <label
                  className="block text-sm font-medium text-slate-600"
                  title="Maximum number of works per store"
                >
                  Max Works
                </label>
                <input
                  type="number"
                  value={globalConstraints.MAX_WORKS || ""}
                  onChange={(e) => {
                    const mw = parseInt(e.target.value);
                    const sundaysCount = Number(globalConstraints.SUNDAYS) || 0;
                    setGlobalConstraints((prev: any) => ({
                      ...prev,
                      MAX_WORKS: mw,
                      MAX_DOESNT_WORK: isNaN(mw)
                        ? undefined
                        : Math.max(0, sundaysCount - mw),
                    }));
                    markDirty();
                  }}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1 text-sm"
                />
              </div>

              <div className="col-span-2">
                <p className="text-sm text-slate-600">
                  Sundays in year:{" "}
                  <span className="font-medium">
                    {globalConstraints.SUNDAYS ?? (sundays.length || 0)}
                  </span>
                </p>
                <p className="text-sm text-slate-600">
                  Max Doesn't Work (calculated):{" "}
                  <span className="font-medium">
                    {globalConstraints.MAX_DOESNT_WORK ??
                      (globalConstraints.SUNDAYS
                        ? globalConstraints.SUNDAYS -
                          (globalConstraints.MAX_WORKS || 0)
                        : sundays.length - (globalConstraints.MAX_WORKS || 0))}
                  </span>
                </p>
              </div>
            </div>
          </div>

          {/* File Uploads */}
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="mb-4 font-semibold">Stores Data (Required)</h3>
              <input
                type="file"
                accept=".json"
                onChange={handleDataFileUpload}
                className="block w-full text-sm text-slate-600 file:rounded file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-semibold"
              />
              <p className="mt-2 text-xs text-slate-500">
                {Object.keys(stores).length} stores loaded
              </p>
            </div>

            {/* clustering removed — handled by algorithm-java */}
          </div>

          {/* Radius Value Calculator */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm mt-4">
            <h3 className="mb-2 font-semibold">
              Radius Value Formula (Required)
            </h3>
            <p className="mb-2 text-xs text-slate-500">
              Python expression used to compute value_for_radius for each store.
              Use the variable 'store'.
            </p>
            <textarea
              value={radiusCalculator}
              onChange={(e) => {
                setRadiusCalculator(e.target.value);
                markDirty();
              }}
              placeholder="return store.get('rating_a', 1) * store.get('rating_b', 2)"
              rows={4}
              className="w-full rounded border border-slate-200 px-3 py-2 text-sm font-mono"
            />
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm mt-4">
            <h3 className="mb-2 font-semibold">Radius Settings</h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label
                  title="How far a huge store draws people when isolated (km)"
                  className="block text-sm font-medium text-slate-600"
                >
                  Max Theoretical Radius (km)
                </label>
                <input
                  type="number"
                  value={generalSettings.MAX_THEORETICAL_RADIUS_KM}
                  onChange={(e) => {
                    setGeneralSettings((prev: any) => ({
                      ...prev,
                      MAX_THEORETICAL_RADIUS_KM: Number(e.target.value),
                    }));
                    markDirty();
                  }}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1 text-sm"
                />
              </div>
              <div>
                <label
                  title="Minimum allowed store radius (km)"
                  className="block text-sm font-medium text-slate-600"
                >
                  Min Radius (km)
                </label>
                <input
                  type="number"
                  value={generalSettings.MIN_RADIUS_KM}
                  onChange={(e) => {
                    setGeneralSettings((prev: any) => ({
                      ...prev,
                      MIN_RADIUS_KM: Number(e.target.value),
                    }));
                    markDirty();
                  }}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1 text-sm"
                />
              </div>
              <div>
                <label
                  title="Higher values make stores shrink more aggressively due to neighbors (0.05-0.2)"
                  className="block text-sm font-medium text-slate-600"
                >
                  Competition Sensitivity
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={generalSettings.COMPETITION_SENSITIVITY}
                  onChange={(e) => {
                    setGeneralSettings((prev: any) => ({
                      ...prev,
                      COMPETITION_SENSITIVITY: Number(e.target.value),
                    }));
                    markDirty();
                  }}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1 text-sm"
                />
              </div>
            </div>
          </div>

          {/* Store List */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm mt-4">
            <h3 className="mb-3 font-semibold">Store List</h3>
            <StoreList
              stores={stores}
              selectedStoreId={selectedStoreId}
              onStoreSelect={handleStoreSelect}
              onDeleteStore={handleDeleteStore}
              constraintsMap={constraintsMap}
            />
          </div>
        </div>

        <div className="md:w-3/5 md:pl-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm sticky top-6">
            <h3 className="mb-3 font-semibold">Map</h3>
            <div className="h-[70vh]">
              <StoreMap
                stores={stores}
                selectedStoreId={selectedStoreId}
                onStoreSelect={handleStoreSelect}
                modalOpen={!!selectedStoreId}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Constraints Editor Modal */}
      {selectedStoreId && (
        <ConstraintsEditorModal
          storeId={selectedStoreId}
          store={stores[selectedStoreId]}
          constraints={
            constraintsMap[selectedStoreId] || { works: [], doesnt_work: [] }
          }
          sundays={sundays}
          onSave={handleConstraintsSave}
          onClose={() => setSelectedStoreId(null)}
        />
      )}
    </div>
  );
}
