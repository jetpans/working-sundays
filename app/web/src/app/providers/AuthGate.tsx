"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useApp } from "@/context/AppContext";

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const { isReady, isAuthenticated } = useApp();
  const pathname = usePathname();
  const router = useRouter();
  const isProtectedRoute = pathname.startsWith("/jobs") || pathname.startsWith("/heartbeat");

  useEffect(() => {
    if (!isReady) return;
    if (pathname === "/login") {
      if (isAuthenticated) router.replace("/jobs");
      return;
    }
    if (isProtectedRoute && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isReady, isAuthenticated, isProtectedRoute, pathname, router]);

  if (!isReady) {
    return (
      <div className="flex flex-1 items-center justify-center px-6 py-12 text-sm text-slate-500">
        Loading session...
      </div>
    );
  }

  if (isProtectedRoute && !isAuthenticated) {
    return null;
  }

  if (pathname === "/login" && isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}