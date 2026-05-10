"use client";

import { useEffect, useState } from "react";

import { useApiFetch } from "@/hooks/useApiFetch";

export default function HeartbeatPage() {
  const [payload, setPayload] = useState<string>("Loading...");
  const apiFetch = useApiFetch();

  useEffect(() => {
    const run = async () => {
      const response = await apiFetch(`/api/heartbeat`, {
        cache: "no-store",
      });
      const json = await response.json();
      setPayload(JSON.stringify(json, null, 2));
    };

    run().catch((e: unknown) => {
      setPayload(e instanceof Error ? e.message : "Request failed");
    });
  }, [apiFetch]);

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-4 px-6 py-10">
      <h1 className="text-2xl font-semibold">Heartbeat</h1>
      <pre className="overflow-auto rounded border bg-zinc-50 p-4 text-xs">
        {payload}
      </pre>
    </main>
  );
}
