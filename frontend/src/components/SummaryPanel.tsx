"use client";

import { useSummary } from "./SummaryContext";
import StatCard from "./StatCard";
import ProgressBar from "./ProgressBar";

export default function SummaryPanel() {
  const { status, loading, error } = useSummary();
  const dash = (n: number | undefined) => (n === undefined ? "–" : n);
  return (
    <aside className="sticky top-0 hidden h-screen w-[330px] shrink-0 overflow-y-auto border-l border-line bg-[#081733]/60 p-7 xl:block">
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
