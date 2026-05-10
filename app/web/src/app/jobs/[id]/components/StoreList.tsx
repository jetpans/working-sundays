"use client";

import { Store, StoreConstraints, getStoreColor } from "@/lib/jobUtils";

interface StoreListProps {
  stores: Record<string, Store>;
  selectedStoreId: string | null;
  onStoreSelect: (storeId: string) => void;
  onDeleteStore: (storeId: string) => void;
  constraintsMap: Record<string, StoreConstraints>;
}

export default function StoreList({
  stores,
  selectedStoreId,
  onStoreSelect,
  onDeleteStore,
  constraintsMap,
}: StoreListProps) {
  const storeEntries = Object.entries(stores);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-3 font-semibold">Stores List</h3>
      <div className="max-h-96 space-y-2 overflow-y-auto">
        {storeEntries.length === 0 ? (
          <p className="text-sm text-slate-500">No stores</p>
        ) : (
          storeEntries.map(([storeId, store]) => {
            const constraints = constraintsMap[storeId];
            const hasConstraints =
              constraints &&
              (constraints.works.length > 0 ||
                constraints.doesnt_work.length > 0);

            return (
              <div
                key={storeId}
                onClick={() => onStoreSelect(storeId)}
                className={`cursor-pointer rounded border p-2 text-xs transition-colors ${
                  selectedStoreId === storeId
                    ? "border-slate-500 bg-slate-50"
                    : "border-slate-200 hover:bg-slate-50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-3 w-3 rounded-full flex-shrink-0"
                        style={{
                          backgroundColor: getStoreColor(store.brand),
                        }}
                      />
                      <p className="font-semibold truncate">
                        {store.name}
                        {store.brand && ` (${store.brand})`}
                      </p>
                    </div>
                    <p className="mt-1 truncate text-slate-600">
                      {store.formatted_address}
                    </p>
                    {hasConstraints && (
                      <p className="mt-1 text-xs text-blue-600">
                        ✓ Constraints set
                      </p>
                    )}
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteStore(storeId);
                    }}
                    className="flex-shrink-0 text-red-600 hover:text-red-800"
                  >
                    ✕
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
