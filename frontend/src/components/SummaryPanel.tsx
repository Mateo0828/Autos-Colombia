"use client";

import { useAuth } from "./AuthContext";
import { useSummary } from "./SummaryContext";
import StatCard from "./StatCard";
import ProgressBar from "./ProgressBar";

export default function SummaryPanel() {
  const { status, loading, error } = useSummary();
  const { user } = useAuth();
  const dash = (n: number | undefined) => (n === undefined ? "–" : n);
  return (
    <aside className="sticky top-0 hidden h-screen w-[330px] shrink-0 overflow-y-auto border-l border-line bg-[#081733]/60 p-7 xl:block">
      {user && (
        <div data-testid="session-box" className="mb-8 rounded-xl border border-line bg-card/60 p-4">
          <p className="text-[10px] font-bold uppercase tracking-widest text-accent">Sesión</p>
          <p className="mt-1 text-sm font-bold">{user.nombre}</p>
          <p className="text-xs text-muted">
            {user.usuario} · {user.rol === "ADMINISTRADOR" ? "Administrador" : "Operador"}
          </p>
        </div>
      )}
      <h2 className="text-lg font-medium">Resumen del parqueadero</h2>
      {error ? (
        <p
          role="alert"
          className="mt-6 rounded-xl border border-danger/40 bg-danger/10 p-4 text-sm text-danger"
        >
          {error}
        </p>
      ) : (
        <>
          <div
            className={`mt-6 grid grid-cols-2 gap-3 ${loading && !status ? "animate-pulse" : ""}`}
          >
            <StatCard label="Celdas totales" value={dash(status?.celdas.total)} />
            <StatCard label="Disponibles" value={dash(status?.celdas.disponibles)} tone="success" />
            <StatCard label="Ocupadas" value={dash(status?.celdas.ocupadas)} tone="warning" />
            <StatCard label="Vehículos dentro" value={dash(status?.vehiculos_dentro)} />
            {status?.celdas.fuera_de_servicio !== undefined && (
              <div className="col-span-2">
                <StatCard label="Fuera de servicio" value={status.celdas.fuera_de_servicio} />
              </div>
            )}
          </div>
          {status && (
            <div className="mt-8 space-y-5">
              <ProgressBar
                label="Carros y camionetas"
                available={status.celdas.carro.disponibles}
                total={status.celdas.carro.total}
              />
              <ProgressBar
                label="Motos"
                available={status.celdas.moto.disponibles}
                total={status.celdas.moto.total}
              />
            </div>
          )}
        </>
      )}
    </aside>
  );
}
