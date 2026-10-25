"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { api, errorMessage } from "@/lib/api";
import type { ParkingStatus } from "@/types/api";

interface SummaryState {
  status: ParkingStatus | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const SummaryContext = createContext<SummaryState | null>(null);

export function SummaryProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<ParkingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pathname = usePathname();

  const refresh = useCallback(async () => {
    try {
      setStatus(await api.status());
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  // Refresh on every screen change (D-11); no polling.
  useEffect(() => {
    refresh();
  }, [pathname, refresh]);

  return (
    <SummaryContext.Provider value={{ status, loading, error, refresh }}>
      {children}
    </SummaryContext.Provider>
  );
}

export function useSummary(): SummaryState {
  const ctx = useContext(SummaryContext);
  if (!ctx) throw new Error("useSummary must be used inside SummaryProvider");
  return ctx;
}
