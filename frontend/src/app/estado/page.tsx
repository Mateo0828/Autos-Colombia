"use client";

import { Car, LayoutGrid } from "lucide-react";
import { percent } from "@/lib/format";
import type { CellGroup } from "@/types/api";
import { useSummary } from "@/components/SummaryContext";
import PageHeader from "@/components/PageHeader";
import StatCard from "@/components/StatCard";
import ProgressBar from "@/components/ProgressBar";
import Alert from "@/components/Alert";

function CapacityCard({
  title,
  group,
  icon: Icon,
}: {
  title: string;
  group: CellGroup;
  icon: typeof Car;
}) {
  return (
    <section className="rounded-2xl border border-line bg-card p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-accent/30 bg-accent/10 text-accent">
            <Icon size={18} />
          </span>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-accent">Capacidad</p>
            <h2 className="text-lg">{title}</h2>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold">{group.total}</p>
          <p className="text-[10px] text-muted">total</p>
        </div>
      </div>
      <div className="mt-6 grid grid-cols-2 border-y border-line">
        <div className="py-5">
          <p className="text-3xl font-bold text-success">{group.disponibles}</p>
          <p className="mt-1 text-xs text-muted">Disponibles</p>
        </div>
        <div className="border-l border-line py-5 pl-5">
          <p className="text-3xl font-bold text-warning">{group.ocupadas}</p>
          <p className="mt-1 text-xs text-muted">Ocupadas</p>
        </div>
      </div>
      <div className="mt-5">
        <ProgressBar label="Disponibilidad" available={group.disponibles} total={group.total} />
      </div>
    </section>
  );
}

export default function StatusPage() {
  const { status, loading, error } = useSummary();
  const c = status?.celdas;

  return (
    <>
      <PageHeader
        title="Estado del parqueadero"
        subtitle="Vista general de la disponibilidad y ocupación por tipo de vehículo."
      />
      {error && <Alert kind="error" title={error} />}
      {!c && loading && <p className="text-sm text-muted">Cargando…</p>}
      {status && c && (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard large label="Celdas totales" value={c.total} note="Capacidad instalada" />
            <StatCard
              large
              label="Disponibles"
              value={c.disponibles}
              tone="success"
              note={`${percent(c.disponibles, c.total).toString().replace(".", ",")}% de capacidad`}
            />
            <StatCard
              large
              label="Ocupadas"
              value={c.ocupadas}
              tone="warning"
              note={`${percent(c.ocupadas, c.total).toString().replace(".", ",")}% de ocupación`}
            />
            <StatCard large label="Vehículos dentro" value={status.vehiculos_dentro} note="Estancias activas" />
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <CapacityCard title="Carros y camionetas" group={c.carro} icon={Car} />
            <CapacityCard title="Motos" group={c.moto} icon={LayoutGrid} />
          </div>
        </>
      )}
    </>
  );
}
