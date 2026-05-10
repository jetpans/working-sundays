"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useApp } from "@/context/AppContext";

export default function AppHeader() {
  const { server, setServer, username, setUsername, isAuthenticated, logout } =
    useApp();
  const [isEditingUsername, setIsEditingUsername] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  const toggleUsernameEdit = () => {
    setIsEditingUsername((current) => !current);
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  if (pathname === "/login") {
    return null;
  }

  return (
    <header className="border-b border-slate-200 bg-white shadow-sm">
      <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3 text-base font-semibold">
          <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white">
            Control
          </span>
          <span>Working Sundays</span>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <label
              className="text-sm font-medium text-slate-600"
              htmlFor="server-input"
            >
              Server
            </label>
            <input
              id="server-input"
              className="w-52 rounded border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none"
              value={server}
              onChange={(event) => setServer(event.target.value)}
              placeholder="localhost:5000"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-600">User</span>
            {isEditingUsername ? (
              <input
                className="w-40 rounded border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
              />
            ) : (
              <span className="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                {username || "-"}
              </span>
            )}
            <button
              className="rounded border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              type="button"
              onClick={toggleUsernameEdit}
            >
              {isEditingUsername ? "Done" : "Edit"}
            </button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-600">Session</span>
            <span
              className={`rounded-full px-3 py-2 text-xs font-semibold ${isAuthenticated ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}
            >
              {isAuthenticated ? "Authenticated" : "Signed out"}
            </span>
            {isAuthenticated && (
              <button
                className="rounded border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                type="button"
                onClick={handleLogout}
              >
                Logout
              </button>
            )}
          </div>
        </div>

        <nav className="flex items-center gap-3">
          <Link
            className="rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
            href="/jobs"
          >
            Jobs
          </Link>
          <a
            className="rounded border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            href={`http://${server}/api/docs`}
            target="_blank"
            rel="noopener noreferrer"
          >
            API Docs
          </a>
          {!isAuthenticated && (
            <Link
              className="rounded border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              href="/login"
            >
              Login
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
