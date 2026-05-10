"use client";

import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import { DEFAULT_SERVER, DEFAULT_USERNAME } from "@/lib/constants";

interface AppContextType {
  server: string;
  setServer: (server: string) => void;
  username: string;
  setUsername: (username: string) => void;
  token: string | null;
  isReady: boolean;
  isAuthenticated: boolean;
  login: (payload: { username: string; token: string }) => void;
  logout: () => void;
  setToken: (token: string | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

const STORAGE_KEYS = {
  server: "working-sundays.server",
  username: "working-sundays.username",
  token: "working-sundays.token",
};

export function AppProvider({ children }: { children: ReactNode }) {
  const [server, setServer] = useState(DEFAULT_SERVER);
  const [username, setUsername] = useState(DEFAULT_USERNAME);
  const [token, setToken] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    try {
      const storedServer = window.localStorage.getItem(STORAGE_KEYS.server);
      const storedUsername = window.localStorage.getItem(STORAGE_KEYS.username);
      const storedToken = window.localStorage.getItem(STORAGE_KEYS.token);

      if (storedServer) setServer(storedServer);
      if (storedUsername) setUsername(storedUsername);
      if (storedToken) setToken(storedToken);
    } finally {
      setIsReady(true);
    }
  }, []);

  useEffect(() => {
    if (!isReady) return;
    window.localStorage.setItem(STORAGE_KEYS.server, server);
  }, [server, isReady]);

  useEffect(() => {
    if (!isReady) return;
    window.localStorage.setItem(STORAGE_KEYS.username, username);
  }, [username, isReady]);

  useEffect(() => {
    if (!isReady) return;
    if (token) {
      window.localStorage.setItem(STORAGE_KEYS.token, token);
    } else {
      window.localStorage.removeItem(STORAGE_KEYS.token);
    }
  }, [token, isReady]);

  const login = ({ username: nextUsername, token: nextToken }: { username: string; token: string }) => {
    setUsername(nextUsername);
    setToken(nextToken);
  };

  const logout = () => {
    setToken(null);
  };

  const value = useMemo(
    () => ({
      server,
      setServer,
      username,
      setUsername,
      token,
      isReady,
      isAuthenticated: Boolean(token),
      login,
      logout,
      setToken,
    }),
    [server, username, token, isReady],
  );

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within AppProvider");
  }
  return context;
}
