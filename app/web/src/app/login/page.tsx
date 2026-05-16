"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useApp } from "@/context/AppContext";

export default function LoginPage() {
  const { server, setServer, login, isAuthenticated } = useApp();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [shouldRedirect, setShouldRedirect] = useState(false);

  useEffect(() => {
    if (shouldRedirect && isAuthenticated) {
      router.replace("/jobs");
    }
  }, [isAuthenticated, router, shouldRedirect]);

  const buildLoginUrl = () => {
    const base = server.trim().replace(/\/+$/, "");
    if (!base) {
      return `${window.location.origin}/api/auth/login`;
    }

    const normalizedBase =
      base.startsWith("http://") || base.startsWith("https://")
        ? base
        : `${window.location.protocol}//${base}`;

    return `${normalizedBase}/api/auth/login`;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await fetch(buildLoginUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload?.success) {
        throw new Error(payload?.error || "Login failed");
      }

      const nextUsername = payload?.data?.user?.username || username;
      const token = payload?.data?.access_token;
      if (!token) throw new Error("Server did not return a session token");

      login({ username: nextUsername, token });
      toast.success("Logged in");
      setShouldRedirect(true);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 items-center justify-center px-6 py-12">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Authentication
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-900">Login</h1>
        <p className="mt-3 text-sm text-slate-600">
          Sign in with one of the trusted file-backed accounts configured on the
          backend.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label
              className="block text-sm font-medium text-slate-700"
              htmlFor="server"
            >
              Server
            </label>
            <input
              id="server"
              className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
              value={server}
              onChange={(event) => setServer(event.target.value)}
              placeholder="sundays.jetpans.com"
            />
          </div>

          <div>
            <label
              className="block text-sm font-medium text-slate-700"
              htmlFor="username"
            >
              Username
            </label>
            <input
              id="username"
              className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
            />
          </div>

          <div>
            <label
              className="block text-sm font-medium text-slate-700"
              htmlFor="password"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}