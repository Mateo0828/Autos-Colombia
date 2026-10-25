"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Car, Search } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import {
  PLATE_ERROR,
  formatDateTime,
  isValidPlate,
  normalizePlate,
  vehicleTypeLabel,
} from "@/lib/format";
import { useOperators } from "@/lib/useOperators";
import type { ActiveStay } from "@/types/api";
import { useSummary } from "@/components/SummaryContext";
import PageHeader from "@/components/PageHeader";
import InfoGrid from "@/components/InfoGrid";
import OperatorSelect from "@/components/OperatorSelect";
import PrimaryButton from "@/components/PrimaryButton";
import Alert from "@/components/Alert";

export default function ExitForm() {
  const { refresh } = useSummary();
  const { operators, error: operatorsError } = useOperators();
  const initialPlate = normalizePlate(useSearchParams().get("placa") ?? "");

  const [plate, setPlate] = useState(initialPlate);
  const [operator, setOperator] = useState<number | null>(null);
  const [stay, setStay] = useState<ActiveStay | null>(null);
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ title: string; detail: string } | null>(null);

  async function search(raw: string) {
    const value = normalizePlate(raw);
    setError(null);
    setSuccess(null);
    setStay(null);
    if (!isValidPlate(value)) {
      setError(PLATE_ERROR);
      return;
    }
    setSearching(true);
    try {
      const r = await api.activeStays();
      const found = r.vehiculos.find((s) => s.vehiculo.placa.toUpperCase() === value);
      if (found) setStay(found);
      else setError("El vehículo no tiene una estancia activa.");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSearching(false);
    }
  }

  // Plate preloaded from "Vehículos dentro": search once on arrival.
  const autoSearched = useRef(false);
  useEffect(() => {
    if (initialPlate && !autoSearched.current) {
      autoSearched.current = true;
      search(initialPlate);
    }
  }, [initialPlate]);

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    if (plate.trim()) search(plate);
  }

  async function onExit() {
    if (!stay || operator === null) return;
    setSubmitting(true);
    setError(null);
    try {
      const r = await api.registerExit({ placa: stay.vehiculo.placa, id_operador: operator });
      setSuccess({
        title: `Salida registrada. Celda ${r.estancia.celda.codigo} liberada`,
        detail: `Salida confirmada ${formatDateTime(r.estancia.fecha_hora_salida).toLowerCase()}`,
      });
      setStay(null);
      refresh();
    } catch (err) {
      setError(errorMessage(err));
      refresh();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        kicker="Control de salida"
        title="Registrar salida"
        subtitle="Busca la estancia activa del vehículo y confirma su salida del parqueadero."
      />

      {success && <Alert kind="success" title={success.title} detail={success.detail} />}
      {error && <Alert kind="error" title={error} />}
      {operatorsError && <Alert kind="error" title={operatorsError} />}

      <section className="mb-4 rounded-2xl border border-line bg-card p-6">
        <p className="text-[10px] font-bold uppercase tracking-widest text-accent">Búsqueda de estancia</p>
        <h2 className="mt-1 text-lg">Buscar vehículo</h2>
        <form onSubmit={onSearch} className="mt-5 grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
          <div>
            <label htmlFor="plate" className="mb-2 block text-xs font-bold">
              Placa
            </label>
            <input
              id="plate"
              value={plate}
              onChange={(e) => setPlate(e.target.value.toUpperCase())}
              placeholder="Ej. ABC123"
              autoComplete="off"
              className="h-11 w-full rounded-xl border border-line bg-[#0a1b3d] px-4 text-sm font-bold uppercase outline-none placeholder:font-normal placeholder:text-muted focus:border-accent"
            />
          </div>
          <div>
            <label htmlFor="operator" className="mb-2 block text-xs font-bold">
              Operador responsable
            </label>
            <OperatorSelect id="operator" operators={operators} value={operator} onChange={setOperator} />
          </div>
          <PrimaryButton type="submit" disabled={!plate.trim() || searching}>
            <Search size={16} />
            {searching ? "Buscando…" : "Buscar vehículo"}
          </PrimaryButton>
        </form>
      </section>

      {stay && (
        <section className="rounded-2xl border border-line bg-card p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-accent/30 bg-accent/10 text-accent">
                <Car size={20} />
              </span>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-accent">Estancia activa</p>
                <h2 className="text-lg">{stay.vehiculo.placa}</h2>
              </div>
            </div>
            <span className="rounded-full border border-success/50 bg-success/10 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-success">
              Dentro
            </span>
          </div>
          <div className="mt-5">
            <InfoGrid
              items={[
                { label: "Marca", value: stay.vehiculo.marca },
                { label: "Color", value: stay.vehiculo.color },
                { label: "Tipo", value: vehicleTypeLabel(stay.vehiculo.tipo_vehiculo) },
                { label: "Celda ocupada", value: stay.celda.codigo },
                { label: "Fecha y hora de entrada", value: formatDateTime(stay.fecha_hora_entrada) },
                { label: "Operador de entrada", value: stay.operador_entrada.nombre },
              ]}
            />
          </div>
          <div className="mt-5 flex items-center justify-between gap-4">
            <p className="text-xs text-muted">
              Al confirmar, la celda <strong className="text-foreground">{stay.celda.codigo}</strong> quedará disponible.
            </p>
            <PrimaryButton onClick={onExit} disabled={operator === null || submitting}>
              {submitting ? "Registrando…" : "Registrar salida"}
              <ArrowRight size={16} />
            </PrimaryButton>
          </div>
          {operator === null && (
            <p className="mt-3 text-right text-xs text-warning">Selecciona un operador para confirmar la salida.</p>
          )}
        </section>
      )}
    </>
  );
}
