"use client";

import { ShieldAlert } from "lucide-react";
import type { Role } from "@/types/api";
import { useAuth } from "./AuthContext";

/** Renders children only for the given role; otherwise "No tienes permiso". */
export default function RoleGate({
  role,
  children,
}: {
  role: Role;
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  if (user?.rol !== role) {
    return (
      <div
        role="alert"
        className="flex flex-col items-center rounded-2xl border border-line bg-card px-6 py-16 text-center"
      >
        <span className="flex h-14 w-14 items-center justify-center rounded-xl bg-danger/10 text-danger">
          <ShieldAlert size={24} />
        </span>
        <p className="mt-5 text-lg font-bold">No tienes permiso</p>
        <p className="mt-2 text-xs text-muted">
          Esta sección es solo para administradores.
        </p>
      </div>
    );
  }
  return <>{children}</>;
}
