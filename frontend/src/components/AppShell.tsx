"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "./AuthContext";
import { SummaryProvider } from "./SummaryContext";
import Sidebar from "./Sidebar";
import SummaryPanel from "./SummaryPanel";

function Guarded({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isLogin = pathname === "/login";

  useEffect(() => {
    if (loading) return;
    if (!user && !isLogin) router.replace("/login");
    if (user && isLogin) router.replace("/entrada");
  }, [user, loading, isLogin, router]);

  if (isLogin) return <>{children}</>;
  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted">
        Cargando…
      </div>
    );
  }
  return (
    <SummaryProvider>
      <div className="flex min-h-screen bg-[radial-gradient(ellipse_at_top,#12326a_0%,#0a1b3d_45%)]">
        <Sidebar />
        <main className="min-w-0 flex-1 px-6 py-12 lg:px-10">
          <div className="mx-auto max-w-[1010px]">{children}</div>
        </main>
        <SummaryPanel />
      </div>
    </SummaryProvider>
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <Guarded>{children}</Guarded>
    </AuthProvider>
  );
}
