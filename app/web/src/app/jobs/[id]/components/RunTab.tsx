"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";
import { useApp } from "@/context/AppContext";
import { useApiFetch } from "@/hooks/useApiFetch";

interface RunTabProps {
  username: string;
  jobId: string;
  server: string;
  onStatusChange?: (status: RunStatus) => void;
}

type RunStatus =
  | "Uninitialized"
  | "Ready"
  | "Running"
  | "Calculating stats"
  | "Error"
  | "Complete";

export default function RunTab({
  username,
  jobId,
  server,
  onStatusChange,
}: RunTabProps) {
  const { token } = useApp();
  const apiFetch = useApiFetch();
  const [status, setStatus] = useState<RunStatus>("Uninitialized");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [isStarting, setIsStarting] = useState(false);
  const [isTerminating, setIsTerminating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const logRef = useRef<HTMLDivElement | null>(null);
  const followLogsRef = useRef(true);

  const isRunning = status === "Running" || status === "Calculating stats";

  const fetchStatus = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/job/${username}/${jobId}/run-info`);
      if (!res.ok) return;
      const body = await res.json();
      if (!body?.success) return;
      const runInfo = body?.data || {};
      if (runInfo.status) {
        const nextStatus = runInfo.status as RunStatus;
        setStatus(nextStatus);
        onStatusChange?.(nextStatus);
      }
      setUpdatedAt(runInfo.updated_at || null);
    } catch {
      // ignore
    }
  }, [apiFetch, username, jobId, onStatusChange]);

  const fetchSavedLogs = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/job/${username}/${jobId}/runlog`);
      if (!res.ok) return;
      const body = await res.json();
      if (!body?.success) return;
      const lines = Array.isArray(body?.data?.lines) ? body.data.lines : [];
      setLogs(lines);
    } catch {
      // ignore
    }
  }, [apiFetch, username, jobId]);

  useEffect(() => {
    fetchStatus();
    fetchSavedLogs();
  }, [fetchStatus, fetchSavedLogs]);

  useEffect(() => {
    const socket = io(`http://${server}`);
    socketRef.current = socket;

    socket.on("connect", () => {
      socket.emit("run_subscribe", { username, jobId, token });
    });

    socket.on(
      "run_status",
      (payload: { status?: RunStatus; updated_at?: string | null }) => {
        if (payload?.status) {
          setStatus(payload.status);
          onStatusChange?.(payload.status);
        }
        setUpdatedAt(payload?.updated_at || null);
      },
    );

    socket.on("run_log", (line: string) => {
      setLogs((prev) => {
        if (prev.length > 0 && prev[prev.length - 1] === line) return prev;
        return [...prev, line];
      });
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [server, username, jobId, token]);

  useEffect(() => {
    if (!followLogsRef.current || !logRef.current) return;
    logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const handleLogScroll = () => {
    const el = logRef.current;
    if (!el) return;
    const threshold = 24;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    followLogsRef.current = distanceFromBottom <= threshold;
  };

  const handleRun = async () => {
    try {
      const proceed = window.confirm(
        "Starting a new run will clear existing results and logs for this job. Do you want to continue?",
      );
      if (!proceed) return;

      setIsStarting(true);
      setError(null);
      setLogs([]);
      const res = await apiFetch(`/api/job/${username}/${jobId}/run`, {
        method: "POST",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || !body?.success) {
        throw new Error(body?.error || "Failed to start run");
      }
      setStatus("Running");
      onStatusChange?.("Running");
      setUpdatedAt(new Date().toISOString());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start run");
    } finally {
      setIsStarting(false);
    }
  };

  const handleTerminate = async () => {
    try {
      setIsTerminating(true);
      setError(null);
      const res = await apiFetch(`/api/job/${username}/${jobId}/terminate`, {
        method: "POST",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || !body?.success) {
        throw new Error(body?.error || "Failed to terminate run");
      }
      setStatus("Error");
      onStatusChange?.("Error");
      setUpdatedAt(new Date().toISOString());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to terminate run");
    } finally {
      setIsTerminating(false);
    }
  };

  const statusLabel = useMemo(() => status || "Uninitialized", [status]);

  return (
    <div className="md:flex md:gap-6">
      <div className="md:w-2/5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold">Run Job</h2>
            {status === "Complete" && (
              <span
                title="Run completed"
                className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-800"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-4 h-4"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 00-1.414-1.414L8 11.172 4.707 7.879a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8z"
                    clipRule="evenodd"
                  />
                </svg>
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleTerminate}
              disabled={!isRunning || isTerminating}
              className="rounded border border-red-200 bg-white px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-60"
            >
              {isTerminating ? "Terminating..." : "Terminate"}
            </button>
            <button
              onClick={handleRun}
              disabled={isStarting || isRunning}
              className="rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {isStarting ? "Starting..." : "Run Algorithm"}
            </button>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-2">
          <h3 className="font-semibold">Metadata</h3>
          <div className="text-sm text-slate-600">
            <div>Status: {statusLabel}</div>
            <div>Updated: {updatedAt || "-"}</div>
            <div>Lines: {logs.length}</div>
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
        </div>
      </div>

      <div className="md:w-3/5">
        <div
          ref={logRef}
          onScroll={handleLogScroll}
          className="rounded-lg border border-slate-200 bg-black p-4 text-green-400 font-mono h-[70vh] overflow-y-auto"
        >
          <div className="text-xs whitespace-pre-wrap">
            {logs.length === 0 ? (
              <p className="text-green-300">
                Log stream will appear here when job runs.
              </p>
            ) : (
              logs.map((line, idx) => <div key={idx}>{line}</div>)
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
