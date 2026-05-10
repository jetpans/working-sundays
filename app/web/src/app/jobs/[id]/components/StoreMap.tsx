"use client";

import dynamic from "next/dynamic";
import { useMemo, useRef, useEffect } from "react";
import { Store, getStoreColor } from "@/lib/jobUtils";

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

interface StoreMapProps {
  stores: Record<string, Store>;
  selectedStoreId: string | null;
  onStoreSelect: (storeId: string) => void;
  modalOpen?: boolean;
}

export default function StoreMap({
  stores,
  selectedStoreId,
  onStoreSelect,
  modalOpen = false,
}: StoreMapProps) {
  const storeEntries = useMemo(() => Object.entries(stores), [stores]);

  const mapRef = useRef<any | null>(null);

  // Toggle map interactivity and z-index when modal opens/closes
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    try {
      const c = map.getContainer();
      if (c && c.style) c.style.zIndex = modalOpen ? "0" : "0";
      if (modalOpen) {
        if (map.dragging) map.dragging.disable();
        if (map.scrollWheelZoom) map.scrollWheelZoom.disable();
        if (map.doubleClickZoom) map.doubleClickZoom.disable();
        if (map.boxZoom) map.boxZoom.disable();
        if (map.keyboard) map.keyboard.disable();
        if (map.touchZoom) map.touchZoom.disable();
      } else {
        if (map.dragging) map.dragging.enable();
        if (map.scrollWheelZoom) map.scrollWheelZoom.enable();
        if (map.doubleClickZoom) map.doubleClickZoom.enable();
        if (map.boxZoom) map.boxZoom.enable();
        if (map.keyboard) map.keyboard.enable();
        if (map.touchZoom) map.touchZoom.enable();
      }
    } catch (e) {
      // ignore
    }
  }, [modalOpen]);

  // Calculate map center from stores
  const mapCenter = useMemo(() => {
    if (storeEntries.length === 0) return [20, 20] as [number, number];

    const lats = storeEntries.map(([_, store]) => store.coordinates[1]);
    const lons = storeEntries.map(([_, store]) => store.coordinates[0]);

    const centerLat = (Math.max(...lats) + Math.min(...lats)) / 2;
    const centerLon = (Math.max(...lons) + Math.min(...lons)) / 2;

    return [centerLat, centerLon] as [number, number];
  }, [storeEntries]);

  // Determine color for a store (brand-based)
  const getColorForStore = (storeId: string) =>
    getStoreColor(stores[storeId]?.brand);

  if (storeEntries.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-center text-slate-500">
        No stores loaded. Upload a data file to see the map.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-3 font-semibold">Store Map</h3>
      <div className="h-96 rounded">
        <MapContainer
          center={mapCenter}
          zoom={13}
          style={{ height: "100%", width: "100%" }}
          whenCreated={(map: any) => {
            mapRef.current = map;
            // ensure map container is below modal
            try {
              const c = map.getContainer();
              if (c && c.style) c.style.zIndex = "0";
            } catch {}
          }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {storeEntries.map(([storeId, store]) => (
            <CircleMarker
              key={storeId}
              center={[store.coordinates[1], store.coordinates[0]]}
              radius={store.radius_km ? Math.max(8, store.radius_km * 2) : 10}
              pathOptions={{
                // brighter fill with a subtle dark stroke for contrast
                fillColor: getColorForStore(storeId),
                color: "rgba(0,0,0,0.5)",
                fillOpacity: selectedStoreId === storeId ? 1 : 0.95,
                weight: selectedStoreId === storeId ? 4 : 2,
                stroke: true,
              }}
              eventHandlers={{
                click: () => onStoreSelect(storeId),
              }}
            >
              <Popup>
                <div className="text-xs">
                  <p className="font-semibold">{store.name}</p>
                  <p className="text-slate-600">{store.brand || "No brand"}</p>
                  <p className="text-slate-500">{store.formatted_address}</p>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

// end
