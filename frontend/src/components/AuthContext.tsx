"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, setUnauthorizedHandler } from "@/lib/api";
import { clearSession, getStoredUser, getToken, saveSession } from "@/lib/session";
import type { Role, SessionUser } from "@/types/api";

interface AuthState {
  user: SessionUser | null;
  /** true while a stored session is being checked with GET /api/auth/me */
  loading: boolean;
  login: (usuario: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (role: Role) => boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);

  // Any 401 (expired, revoked, deactivated) ends the session locally.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null);
      router.replace("/login?expirada=1");
    });
    return () => setUnauthorizedHandler(null);
  }, [router]);

  // Restore the session on first load: trust the server, not the stored copy.
  useEffect(() => {
    let cancelled = false;
    if (!getToken()) {
      setLoading(false);
      return;
    }
    const cached = getStoredUser();
    if (cached) setUser(cached);
    api
      .me()
      .then((r) => !cancelled && setUser(r.usuario))
      .catch(() => {
        // A 401 already cleared the session through the handler;
        // on network errors the cached user is kept.
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (usuario: string, password: string) => {
    const r = await api.login(usuario, password);
    saveSession(r.token, r.usuario);
    setUser(r.usuario);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // Even if the server is unreachable the local session is dropped.
    }
    clearSession();
    setUser(null);
    router.replace("/login");
  }, [router]);

  const hasRole = useCallback((role: Role) => user?.rol === role, [user]);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
