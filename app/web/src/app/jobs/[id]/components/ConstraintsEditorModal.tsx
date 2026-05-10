"use client";

import { useState, useMemo } from "react";
import { Store, StoreConstraints, formatSundayDate } from "@/lib/jobUtils";

interface ConstraintsEditorModalProps {
  storeId: string;
  store: Store;
  constraints: StoreConstraints;
  sundays: Date[];
  onSave: (storeId: string, constraints: StoreConstraints) => void;
  onClose: () => void;
}

type SundayState = "default" | "works" | "doesnt_work";

export default function ConstraintsEditorModal({
  storeId,
  store,
  constraints,
  sundays,
  onSave,
  onClose,
}: ConstraintsEditorModalProps) {
  const [sundayStates, setSundayStates] = useState<Record<number, SundayState>>(
    () => {
      const states: Record<number, SundayState> = {};
      sundays.forEach((_, idx) => {
        if (constraints.works.includes(idx)) {
          states[idx] = "works";
        } else if (constraints.doesnt_work.includes(idx)) {
          states[idx] = "doesnt_work";
        } else {
          states[idx] = "default";
        }
      });
      return states;
    },
  );

  const getSundayColor = (state: SundayState) => {
    switch (state) {
      case "works":
        return "bg-green-100 border-green-300 text-green-900";
      case "doesnt_work":
        return "bg-red-100 border-red-300 text-red-900";
      case "default":
        return "bg-yellow-50 border-yellow-200 text-slate-700";
    }
  };

  const getSundayLabel = (state: SundayState) => {
    switch (state) {
      case "works":
        return "✓ Works";
      case "doesnt_work":
        return "✕ Doesn't work";
      case "default":
        return "—";
    }
  };

  const toggleSundayState = (sundayIdx: number) => {
    setSundayStates((prev) => {
      const current = prev[sundayIdx] || "default";
      const next: SundayState =
        current === "default"
          ? "works"
          : current === "works"
            ? "doesnt_work"
            : "default";
      return {
        ...prev,
        [sundayIdx]: next,
      };
    });
  };

  const handleSave = () => {
    const works = Object.entries(sundayStates)
      .filter(([_, state]) => state === "works")
      .map(([idx]) => parseInt(idx));

    const doesnt_work = Object.entries(sundayStates)
      .filter(([_, state]) => state === "doesnt_work")
      .map(([idx]) => parseInt(idx));

    onSave(storeId, { works, doesnt_work });
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-transparent backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-lg bg-white/95 shadow-lg">
        {/* Header */}
        <div className="border-b border-slate-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">{store.name}</h2>
              <p className="text-xs text-slate-600">
                {store.brand && <span>{store.brand} • </span>}
                {store.formatted_address}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Legend */}
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <p className="mb-2 text-xs font-semibold text-slate-600">
            Click on Sundays to toggle:
          </p>
          <div className="flex gap-4">
            <div className="flex items-center gap-2 text-xs">
              <div className="h-3 w-3 rounded bg-green-100" />
              <span>Must work</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="h-3 w-3 rounded bg-yellow-50 border border-yellow-200" />
              <span>No preference</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="h-3 w-3 rounded bg-red-100" />
              <span>Must not work</span>
            </div>
          </div>
        </div>

        {/* Sundays Grid */}
        <div className="p-4">
          <div className="grid grid-cols-4 gap-2">
            {sundays.map((date, idx) => (
              <button
                key={idx}
                onClick={() => toggleSundayState(idx)}
                className={`rounded border p-2 text-center text-xs font-medium transition-colors ${getSundayColor(
                  sundayStates[idx] || "default",
                )}`}
              >
                <div className="font-semibold">Sunday {idx}</div>
                <div className="text-xs opacity-75">
                  {formatSundayDate(date)}
                </div>
                <div className="mt-1 text-xs font-normal">
                  {getSundayLabel(sundayStates[idx] || "default")}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 bg-slate-50 p-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          >
            Save Constraints
          </button>
        </div>
      </div>
    </div>
  );
}
