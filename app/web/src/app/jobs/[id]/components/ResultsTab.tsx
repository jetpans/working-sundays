"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState, Fragment } from "react";
import { useApiFetch } from "@/hooks/useApiFetch";
import { getStoreColor } from "@/lib/jobUtils";
import {
  DeltaDistributionChart,
  FitnessHistoryChart,
  type FitnessPoint,
  type SundayDeltaPoint,
} from "./ResultsCharts";

const MapContainer = dynamic(
  () => import("react-leaflet").then((m) => m.MapContainer),
  { ssr: false },
 ) as any;
const TileLayer = dynamic(
  () => import("react-leaflet").then((m) => m.TileLayer),
  { ssr: false },
 ) as any;
const CircleMarker = dynamic(
  () => import("react-leaflet").then((m) => m.CircleMarker),
  { ssr: false },
 ) as any;
const Popup = dynamic(() => import("react-leaflet").then((m) => m.Popup), {
  ssr: false,
}) as any;
const Polygon = dynamic(() => import("react-leaflet").then((m) => m.Polygon), {
  ssr: false,
}) as any;

interface ResultsTabProps {
  username: string;
  jobId: string;
  server: string;
}

function isSolutionResultFile(fileName: string): boolean {
  return fileName.endsWith(".json") && !fileName.startsWith("_");
}

export default function ResultsTab({
  username,
  jobId,
  server,
}: ResultsTabProps) {
  const apiFetch = useApiFetch();
  const [results, setResults] = useState<string[]>([]);
  const [randomFile, setRandomFile] = useState<string | null>(null);
  const [optFile, setOptFile] = useState<string | null>(null);
  const [showRandom, setShowRandom] = useState(true);
  const [showOpt, setShowOpt] = useState(true);
  const [selectedSundays, setSelectedSundays] = useState<number[]>([]);
  const [sundaysCount, setSundaysCount] = useState(0);
  const [stores, setStores] = useState<Record<string, any> | null>(null);
  const [randomPolygons, setRandomPolygons] = useState<any[]>([]);
  const [optPolygons, setOptPolygons] = useState<any[]>([]);
  const [stats, setStats] = useState<any | null>(null);
  const [statsState, setStatsState] = useState<
    "idle" | "loading" | "calculating" | "ready" | "error"
  >("idle");
  const [statsMessage, setStatsMessage] = useState<string | null>(null);
  const [fitnessPoints, setFitnessPoints] = useState<FitnessPoint[]>([]);
  const [fitnessMessage, setFitnessMessage] = useState<string | null>(null);
  const [mapHover, setMapHover] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await apiFetch(`/api/job/${username}/${jobId}`);
        if (res.ok) {
          const body = await res.json();
          const data = body?.data?.data || null;
          const constraints = body?.data?.constraints || null;
          if (data) setStores(data);
          if (constraints && constraints.SUNDAYS)
            setSundaysCount(constraints.SUNDAYS);
        }
      } catch (e) {
        // ignore
      }
    };
    load();
  }, [server, username, jobId]);

  useEffect(() => {
    const loadList = async () => {
      try {
        const res = await apiFetch(`/api/job/${username}/${jobId}/results`);
        if (!res.ok) return;
        const body = await res.json();
        const files: string[] = body?.data || [];
        const solutionFiles = files.filter(isSolutionResultFile);
        setResults(solutionFiles);
        // pick defaults if present
        if (solutionFiles.includes("random_start.json"))
          setRandomFile("random_start.json");
        else if (solutionFiles.length > 0) setRandomFile(solutionFiles[0]);
        if (solutionFiles.includes("solution.json")) setOptFile("solution.json");
        else if (solutionFiles.length > 0) setOptFile(solutionFiles[solutionFiles.length - 1]);
      } catch {}
    };
    loadList();
  }, [server, username, jobId]);

  useEffect(() => {
    const loadFitnessHistory = async () => {
      try {
        setFitnessMessage(null);
        const res = await apiFetch(
          `/api/job/${username}/${jobId}/results/fitness-history`,
        );
        const body = await res.json();
        if (!res.ok || body?.success === false) {
          setFitnessPoints([]);
          setFitnessMessage(body?.error || `Failed to load fitness history (${res.status})`);
          return;
        }

        setFitnessPoints(body?.data?.points || []);
      } catch {
        setFitnessPoints([]);
        setFitnessMessage("Failed to load fitness history.");
      }
    };

    loadFitnessHistory();
  }, [server, username, jobId]);

  // load polygons and stats when files change
  useEffect(() => {
    let cancelled = false;
    let statsPollTimer: ReturnType<typeof setTimeout> | null = null;

    const loadPolys = async (
      name: string | null,
      setter: (v: any[]) => void,
    ) => {
      if (!name) return setter([]);
      try {
        const res = await apiFetch(
          `/api/job/${username}/${jobId}/results/polygons?name=${encodeURIComponent(name)}`,
        );
        if (!res.ok) return setter([]);
        const body = await res.json();
        const sundays = body?.data?.sundays || [];
        setter(sundays);
      } catch {
        setter([]);
      }
    };

    loadPolys(randomFile, setRandomPolygons);
    loadPolys(optFile, setOptPolygons);

    const loadStats = async () => {
      try {
        if (!randomFile || !optFile) {
          setStats(null);
          setStatsState("idle");
          setStatsMessage("Select both result files to calculate statistics.");
          return;
        }
        setStatsState((current) =>
          current === "calculating" ? "calculating" : "loading",
        );
        setStatsMessage(null);
        const res = await apiFetch(
          `/api/job/${username}/${jobId}/results/stats?random=${encodeURIComponent(randomFile)}&optimized=${encodeURIComponent(optFile)}`,
        );
        const body = await res.json();
        if (cancelled) return;

        if (res.status === 202 || body?.status === "calculating") {
          setStats(null);
          setStatsState("calculating");
          setStatsMessage("Statistics are being calculated. This can take a moment for large jobs.");
          statsPollTimer = setTimeout(loadStats, 3000);
          return;
        }

        if (!res.ok || body?.success === false) {
          setStats(null);
          setStatsState("error");
          setStatsMessage(body?.error || `Failed to load statistics (${res.status})`);
          return;
        }

        setStats(body?.data || null);
        setStatsState(body?.data ? "ready" : "idle");
        setStatsMessage(body?.data ? null : "No statistics were returned.");
      } catch {
        if (cancelled) return;
        setStats(null);
        setStatsState("error");
        setStatsMessage("Failed to load statistics.");
      }
    };

    loadStats();

    return () => {
      cancelled = true;
      if (statsPollTimer) clearTimeout(statsPollTimer);
    };
  }, [server, username, jobId, randomFile, optFile]);

  const mapCenter = useMemo(() => {
    if (!stores) return [45.1, 16.0];
    const vals = Object.values(stores) as any[];
    const lats = vals.map((s) => s.coordinates[1]);
    const lons = vals.map((s) => s.coordinates[0]);
    const centerLat = (Math.max(...lats) + Math.min(...lats)) / 2;
    const centerLon = (Math.max(...lons) + Math.min(...lons)) / 2;
    return [centerLat, centerLon];
  }, [stores]);

  const findPolysForSunday = (arr: any[], sunday: number) =>
    (arr && arr.find((s) => s && s.sunday === sunday)?.polygons) || [];

  const currentRandomPolysFor = (sunday: number) =>
    findPolysForSunday(randomPolygons, sunday);
  const currentOptPolysFor = (sunday: number) =>
    findPolysForSunday(optPolygons, sunday);

  const selectedSundayStats = useMemo(() => {
    const perSunday = Array.isArray(stats?.per_sunday) ? stats.per_sunday : [];
    return selectedSundays
      .map((sunday) => {
        const entry = perSunday.find((item: any) => item?.sunday === sunday);
        if (!entry) return null;

        const random = Number(entry.random ?? 0);
        const optimized = Number(entry.optimized ?? 0);
        const delta = Number(entry.delta ?? optimized - random);
        const percent =
          entry.delta_pct ?? (random === 0 ? null : (delta / Math.abs(random)) * 100);

        return {
          sunday,
          random,
          optimized,
          delta,
          percent,
        };
      })
      .filter(Boolean) as Array<{
      sunday: number;
      random: number;
      optimized: number;
      delta: number;
      percent: number | null;
    }>;
  }, [selectedSundays, stats]);

  const sundayDeltaPoints = useMemo(() => {
    const perSunday = Array.isArray(stats?.per_sunday) ? stats.per_sunday : [];
    return perSunday
      .map((entry: any) => {
        const sunday = Number(entry?.sunday);
        const delta = Number(entry?.delta);
        if (!Number.isFinite(sunday) || !Number.isFinite(delta)) return null;
        return { sunday, delta };
      })
      .filter(Boolean) as SundayDeltaPoint[];
  }, [stats]);

  const formatStat = (value: number | null | undefined) =>
    value === null || value === undefined || Number.isNaN(value)
      ? "n/a"
      : value.toFixed(3);

  const formatPercent = (value: number | null | undefined) =>
    value === null || value === undefined || Number.isNaN(value)
      ? "n/a"
      : `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;

  const improvementRatio = (random: number, optimized: number) => {
    const baseline = Math.max(Math.abs(random), Math.abs(optimized), 1);
    const ratio = Math.min(Math.abs(optimized - random) / baseline, 1);
    return Math.max(ratio, 0.05);
  };

  const sundayColors = useMemo(() => {
    const out: string[] = [];
    for (let i = 0; i < Math.max(1, sundaysCount); i++) {
      const hue = (i * 360) / Math.max(1, sundaysCount);
      out.push(`hsl(${hue},60%,60%)`);
    }
    return out;
  }, [sundaysCount]);

  return (
    <div className="md:flex md:gap-6">
      <div className="md:w-2/5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Results</h2>
        </div>

        {/* Statistics moved to top for visibility */}
        <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
          <h4 className="font-semibold text-lg">Statistics</h4>
          {stats ? (
            <div className="space-y-3 mt-2">
              <div className="text-sm text-slate-700">
                <div className="text-base font-medium">Overall</div>
                <div className="mt-1">
                  Random:{" "}
                  <span className="font-semibold">
                    {stats.overall?.random?.toFixed(3)}
                  </span>
                </div>
                <div>
                  Optimized:{" "}
                  <span className="font-semibold">
                    {stats.overall?.optimized?.toFixed(3)}
                  </span>
                </div>
                <div>
                  Delta:{" "}
                  <span className="font-semibold">
                    {stats.overall?.delta?.toFixed(3)}
                  </span>
                </div>
              </div>

              <div>
                <div className="text-base font-medium">Delta summary</div>
                <div className="mt-1 grid grid-cols-2 gap-2 text-sm">
                  <div>
                    Mean:{" "}
                    <span className="font-semibold">
                      {stats.delta_summary?.mean?.toFixed(3)}
                    </span>
                  </div>
                  <div>
                    Median:{" "}
                    <span className="font-semibold">
                      {stats.delta_summary?.median?.toFixed(3)}
                    </span>
                  </div>
                  <div>
                    Min:{" "}
                    <span className="font-semibold">
                      {stats.delta_summary?.min?.toFixed(3)}
                    </span>
                  </div>
                  <div>
                    Max:{" "}
                    <span className="font-semibold">
                      {stats.delta_summary?.max?.toFixed(3)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : statsState === "loading" || statsState === "calculating" ? (
            <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              {statsMessage || "Statistics are being calculated."}
            </div>
          ) : statsState === "error" ? (
            <div className="rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              {statsMessage || "Statistics could not be calculated."}
            </div>
          ) : (
            <div className="text-sm text-slate-500">
              {statsMessage || "No stats available"}
            </div>
          )}

          {/* quick toggles */}
          <div className="pt-2">
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm">
                <input
                  id="showRandom"
                  type="checkbox"
                  checked={showRandom}
                  onChange={(e) => setShowRandom(e.target.checked)}
                />{" "}
                <span>Show Random</span>
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  id="showOpt"
                  type="checkbox"
                  checked={showOpt}
                  onChange={(e) => setShowOpt(e.target.checked)}
                />{" "}
                <span>Show Optimized</span>
              </label>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
          <div>
            <h4 className="font-semibold text-lg">Fitness Over Iterations</h4>
            <div className="text-sm text-slate-500">
              Global fitness from results/fitness_history.csv.
            </div>
          </div>
          {fitnessMessage ? (
            <div className="rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              {fitnessMessage}
            </div>
          ) : (
            <FitnessHistoryChart points={fitnessPoints} />
          )}
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
          <div>
            <h4 className="font-semibold text-lg">Sunday Delta Distribution</h4>
            <div className="text-sm text-slate-500">
              Optimized minus random per Sunday, centered at zero.
            </div>
          </div>
          {statsState === "loading" || statsState === "calculating" ? (
            <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              Waiting for statistics before drawing the distribution.
            </div>
          ) : statsState === "error" ? (
            <div className="rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              {statsMessage || "Statistics could not be calculated."}
            </div>
          ) : (
            <DeltaDistributionChart points={sundayDeltaPoints} />
          )}
        </div>
      </div>

      <div className="md:w-3/5">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div
            className="relative"
            onMouseEnter={() => setMapHover(true)}
            onMouseLeave={() => setMapHover(false)}
          >
            <div className="h-[70vh] rounded">
              <MapContainer
                center={mapCenter as any}
                zoom={12}
                style={{ height: "100%", width: "100%" }}
              >
                <TileLayer
                  attribution="&copy; OpenStreetMap"
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {stores &&
                  Object.entries(stores).map(([id, s]) => (
                    <CircleMarker
                      key={id}
                      center={[s.coordinates[1], s.coordinates[0]]}
                      radius={6}
                      pathOptions={{
                        fillColor: getStoreColor(s.brand),
                        color: "#111",
                        weight: 1,
                        fillOpacity: 0.9,
                      }}
                    >
                      <Popup>
                        <div className="text-xs">
                          <div className="font-semibold">{s.name}</div>
                          <div className="text-slate-600">
                            {s.formatted_address}
                          </div>
                        </div>
                      </Popup>
                    </CircleMarker>
                  ))}

                {/* Polygons per selected sunday */}
                {selectedSundays.length === 0 && <></>}
                {selectedSundays.map((s) => {
                  const color = sundayColors[s] || "#888";
                  const randPolys = currentRandomPolysFor(s);
                  const optPolys = currentOptPolysFor(s);
                  return (
                    <Fragment key={`s-${s}`}>
                      {showRandom &&
                        randPolys.map((p: any) => (
                          <Polygon
                            key={`r-${s}-${p.store_id}`}
                            positions={p.coords.map((c: any) => [c[0], c[1]])}
                            pathOptions={{
                              color: color,
                              fillColor: color,
                              fillOpacity: 0.08,
                              weight: 1,
                            }}
                          />
                        ))}

                      {showOpt &&
                        optPolys.map((p: any) => (
                          <Polygon
                            key={`o-${s}-${p.store_id}`}
                            positions={p.coords.map((c: any) => [c[0], c[1]])}
                            pathOptions={{
                              color: color,
                              fillColor: color,
                              fillOpacity: 0.22,
                              weight: 2,
                            }}
                          />
                        ))}
                    </Fragment>
                  );
                })}
              </MapContainer>
            </div>
            {/* ← closes h-[70vh] div */}

            {/* Overlays are outside the map div so Leaflet's stacking context can't bury them.
                Inline style z-index is used because Leaflet overrides Tailwind z-* classes. */}
            {mapHover && (
              <div
                className="absolute top-3 left-3 bg-white p-2 rounded shadow"
                style={{ zIndex: 1000 }}
              >
                <div className="text-xs font-medium mb-1">Sundays</div>
                <div className="grid grid-cols-6 gap-1">
                  {Array.from({ length: Math.max(1, sundaysCount) }).map(
                    (_, i) => (
                      <button
                        key={i}
                        onClick={() => {
                          setSelectedSundays((prev) => {
                            if (prev.includes(i))
                              return prev.filter((x) => x !== i);
                            return [...prev, i].sort((a, b) => a - b);
                          });
                        }}
                        className={`text-xs py-1 px-2 rounded border ${selectedSundays.includes(i) ? "bg-slate-900 text-white" : "bg-white text-slate-700"}`}
                      >
                        {i + 1}
                      </button>
                    ),
                  )}
                </div>
              </div>
            )}

            <div
              className="absolute top-3 right-3 bg-white p-2 rounded shadow text-sm"
              style={{ zIndex: 1000 }}
            >
              {selectedSundays.length === 0 ? (
                <div className="text-slate-500">No sundays selected</div>
              ) : (
                <div className="space-y-2 min-w-[280px] max-w-[360px]">
                  {selectedSundays.map((s) => (
                    <div key={`selected-${s}`} className="flex items-center gap-2">
                      <div
                        style={{
                          width: 14,
                          height: 14,
                          background: sundayColors[s],
                          borderRadius: 3,
                        }}
                      />
                      <div>Sunday {s + 1}</div>
                    </div>
                  ))}

                  <div className="border-t border-slate-200 pt-2 space-y-2">
                    {selectedSundayStats.length === 0 ? (
                      <div className="text-slate-500 text-xs">
                        {statsState === "calculating"
                          ? "Stats are being calculated"
                          : "Stats not available yet"}
                      </div>
                    ) : (
                      selectedSundayStats.map((entry) => {
                        const gain = improvementRatio(entry.random, entry.optimized);
                        const randomShare = `${Math.round((1 - gain) * 100)}%`;
                        const optimizedShare = `${Math.round(gain * 100)}%`;

                        return (
                          <div
                            key={`stats-${entry.sunday}`}
                            className="rounded border border-slate-200 bg-slate-50 p-2"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <div className="font-medium text-slate-900">
                                Sunday {entry.sunday + 1}
                              </div>
                              <div className="text-xs font-semibold text-emerald-700">
                                {formatPercent(entry.percent)}
                              </div>
                            </div>

                            <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-slate-700">
                              <div>
                                <div className="text-slate-500">Random</div>
                                <div className="font-semibold">{formatStat(entry.random)}</div>
                              </div>
                              <div>
                                <div className="text-slate-500">Optimized</div>
                                <div className="font-semibold">{formatStat(entry.optimized)}</div>
                              </div>
                              <div>
                                <div className="text-slate-500">Delta</div>
                                <div className={`font-semibold ${entry.delta >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                                  {entry.delta >= 0 ? "+" : ""}{formatStat(entry.delta)}
                                </div>
                              </div>
                            </div>

                            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
                              <div className="flex h-full w-full">
                                <div
                                  className="bg-slate-400"
                                  style={{ width: randomShare }}
                                  title={`Random: ${formatStat(entry.random)}`}
                                />
                                <div
                                  className="bg-emerald-500"
                                  style={{ width: optimizedShare }}
                                  title={`Optimized: ${formatStat(entry.optimized)}`}
                                />
                              </div>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
          {/* ← closes relative div */}

          {/* file selectors under map */}
          <div className="mt-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm">Random file</label>
                <select
                  className="w-full rounded border p-2"
                  value={randomFile || ""}
                  onChange={(e) => setRandomFile(e.target.value)}
                >
                  <option value="">-- none --</option>
                  {results.map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm">Optimized file</label>
                <select
                  className="w-full rounded border p-2"
                  value={optFile || ""}
                  onChange={(e) => setOptFile(e.target.value)}
                >
                  <option value="">-- none --</option>
                  {results.map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
