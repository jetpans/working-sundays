"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "@/context/AppContext";

function buildApiUrl(server: string, path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const baseServer = server.trim().replace(/\/+$/, "");

  if (!baseServer) {
    return `${window.location.origin}${normalizedPath}`;
  }

  const normalizedServer = baseServer.startsWith("http://") || baseServer.startsWith("https://")
    ? baseServer
    : `${window.location.protocol}//${baseServer}`;

  return `${normalizedServer}${normalizedPath}`;
}

export function useApiFetch() {
  const { server, token, logout } = useApp();
  const router = useRouter();

  return useCallback(
    async (path: string, options: RequestInit = {}) => {
      const headers = new Headers(options.headers || {});
      if (token) {
        headers.set("Authorization", `Bearer ${token}`);
      }
      if (
        options.body &&
        !headers.has("Content-Type") &&
        !(options.body instanceof FormData)
      ) {
        headers.set("Content-Type", "application/json");
      }

      const response = await fetch(buildApiUrl(server, path), {
        ...options,
        headers,
      });

      if (response.status === 401) {
        logout();
        router.push("/login");
      }

      return response;
    },
    [logout, router, server, token],
  );
}