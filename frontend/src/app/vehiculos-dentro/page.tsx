"use client";

import { useEffect, useState } from "react";
import { Car } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { ActiveStay } from "@/types/api";
import PageHeader from "@/components/PageHeader";
import VehiclesTable from "@/components/VehiclesTable";
import Alert from "@/components/Alert";

export default function InsidePage() {
  const [stays, setStays] = useState<ActiveStay[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .activeStays()
      .then((r) => setStays(r.vehiculos))
      .catch((e) => setError(errorMessage(e)));
  }, []);

  return (
    <>
      <PageHeader
        kicker="Ocupación actual"
        title="Vehículos dentro del parqueadero"
        subtitle="Consulta las estancias activas y registra salidas rápidamente."
      />
      {error && <Alert kind="error" title={error} />}
      {!stays && !error && <p className="text-sm text-muted">Cargando…</p>}
      {stays && (
        <>
          <p className="mb-4 text-sm text-muted">
            <span className="text-2xl font-bold text-accent">{stays.length}</span>{" "}
            {stays.length === 1 ? "vehículo dentro" : "vehículos dentro"}
          </p>
          {stays.length === 0 ? (
            <div className="flex flex-col items-center rounded-2xl border border-line bg-card px-6 py-16 text-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-xl bg-white/5 text-muted">
                <Car size={24} />
              </span>
              <p className="mt-5">No hay vehículos dentro del parqueadero</p>
              <p className="mt-2 text-xs text-muted">Las nuevas entradas aparecerán aquí.</p>
            </div>
          ) : (
            <VehiclesTable stays={stays} />
          )}
        </>
      )}
    </>
  );
}
