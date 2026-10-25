"use client";

import { useState } from "react";
import { ArrowRight, Check, Info, Search, X } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import {
  PLATE_ERROR,
  formatDateTime,
  formatDocument,
  isValidPlate,
  normalizePlate,
  vehicleTypeLabel,
} from "@/lib/format";
import { useOperators } from "@/lib/useOperators";
import type { Cell, EntryValidation } from "@/types/api";
import { useSummary } from "@/components/SummaryContext";
import PageHeader from "@/components/PageHeader";
import StepCard from "@/components/StepCard";
import InfoGrid from "@/components/InfoGrid";
import CellChip from "@/components/CellChip";
import OperatorSelect from "@/components/OperatorSelect";
import PrimaryButton from "@/components/PrimaryButton";
import Alert from "@/components/Alert";

export default function EntryPage() {
  const { refresh } = useSummary();
  const { operators, error: operatorsError } = useOperators();

  const [plate, setPlate] = useState("");
  const [checking, setChecking] = useState(false);
  const [validation, setValidation] = useState<EntryValidation | null>(null);
  const [cells, setCells] = useState<Cell[]>([]);
  const [cell, setCell] = useState<string | null>(null);
  const [operator, setOperator] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ title: string; detail: string } | null>(null);

  const vehicle = validation?.vehiculo ?? null;
  const canEnter = validation?.puede_ingresar === true && vehicle !== null;

  async function loadCells(type: NonNullable<typeof vehicle>["tipo_vehiculo"]) {
    const r = await api.availableCells(type);
    setCells(r.celdas);
    return r.celdas;
  }

  async function onCheck(e: React.FormEvent) {
    e.preventDefault();
    const value = normalizePlate(plate);
    if (!value) return;
    setError(null);
    setSuccess(null);
    setValidation(null);
    setCells([]);
    setCell(null);
    if (!isValidPlate(value)) {
      setError(PLATE_ERROR);
      return;
    }
    setChecking(true);
    try {
      const v = await api.validateEntry(value);
      setValidation(v);
      if (v.puede_ingresar && v.vehiculo) await loadCells(v.vehiculo.tipo_vehiculo);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setChecking(false);
    }
  }

  async function onRegister() {
    if (!vehicle || !cell || operator === null) return;
    setSubmitting(true);
    setError(null);
    try {
      const r = await api.registerEntry({
        placa: vehicle.placa,
        codigo_celda: cell,
        id_operador: operator,
      });
      setSuccess({
        title: `Entrada registrada. Celda ${r.estancia.celda.codigo} ocupada`,
        detail: `Ingreso confirmado ${formatDateTime(r.estancia.fecha_hora_entrada).toLowerCase()}`,
      });
      setValidation(null);
      setCells([]);
      setCell(null);
      setPlate("");
      refresh();
    } catch (err) {
      setError(errorMessage(err));
      // The chosen cell may have been taken meanwhile: reload the list.
      try {
        await loadCells(vehicle.tipo_vehiculo);
        setCell(null);
      } catch {
        // keep the original error message
      }
      refresh();
    } finally {
      setSubmitting(false);
    }
  }

  const checks = validation
    ? [
        ["Vehículo registrado", validation.validaciones.vehiculo_registrado],
        ["Mensualidad activa", validation.validaciones.mensualidad_activa],
        ["Sin estancia activa", validation.validaciones.sin_estancia_activa],
      ]
    : [];

  return (
    <>
      <PageHeader
        kicker="Control de acceso"
        title="Registrar entrada"
        subtitle="Consulta el vehículo, verifica su mensualidad y asigna una celda disponible."
      />

      {success && <Alert kind="success" title={success.title} detail={success.detail} />}
      {error && <Alert kind="error" title={error} />}
      {operatorsError && <Alert kind="error" title={operatorsError} />}

      <StepCard step={1} kicker="Primer paso" title="Consultar vehículo">
        <form onSubmit={onCheck}>
          <label htmlFor="plate" className="mb-2 block text-xs font-bold">
            Placa
          </label>
          <div className="flex gap-3">
            <input
              id="plate"
              value={plate}
              onChange={(e) => setPlate(e.target.value.toUpperCase())}
              placeholder="Ej. ABC123"
              autoComplete="off"
              className="h-11 min-w-0 flex-1 rounded-xl border border-line bg-[#0a1b3d] px-4 text-sm font-bold uppercase outline-none placeholder:font-normal placeholder:text-muted focus:border-accent"
            />
            <PrimaryButton type="submit" disabled={!plate.trim() || checking}>
              <Search size={16} />
              {checking ? "Consultando…" : "Consultar vehículo"}
            </PrimaryButton>
          </div>
        </form>
      </StepCard>

      {vehicle ? (
        <StepCard
          step={2}
          kicker="Verificación"
          title="Datos del vehículo"
          aside={
            <span
              className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-wider ${
                vehicle.estado_mensualidad === "ACTIVA"
                  ? "border-success/50 bg-success/10 text-success"
                  : "border-danger/50 bg-danger/10 text-danger"
              }`}
            >
              {vehicle.estado_mensualidad}
            </span>
          }
        >
          <InfoGrid
            items={[
              { label: "Placa", value: vehicle.placa },
              { label: "Marca", value: vehicle.marca },
              { label: "Color", value: vehicle.color },
              { label: "Tipo de vehículo", value: vehicleTypeLabel(vehicle.tipo_vehiculo) },
              { label: "Cliente", value: vehicle.cliente.nombre },
              { label: "Documento", value: formatDocument(vehicle.cliente.documento) },
            ]}
          />
          <p className="mt-4 flex items-center gap-3 rounded-xl bg-black/20 px-4 py-3 text-xs text-muted">
            <Info size={15} className="shrink-0 text-warning" />
            Verifique físicamente que la placa, la marca, el color y el tipo coincidan con el vehículo.
          </p>
          <ul className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs">
            {checks.map(([label, ok]) => (
              <li key={String(label)} className={`flex items-center gap-2 ${ok ? "text-success" : "text-danger"}`}>
                {ok ? <Check size={14} /> : <X size={14} />}
                <span className="text-foreground/80">{label}</span>
              </li>
            ))}
          </ul>
          {!validation?.puede_ingresar && (
            <p role="alert" className="mt-4 text-sm font-bold text-danger">
              {validation?.motivo}
            </p>
          )}
        </StepCard>
      ) : validation ? (
        <StepCard step={2} kicker="Verificación" title="Datos del vehículo">
          <p role="alert" className="text-sm font-bold text-danger">
            {validation.motivo}
          </p>
        </StepCard>
      ) : (
        <StepCard
          step={2}
          kicker="Verificación"
          title="Datos del vehículo"
          disabled
          placeholder="Consulta una placa para visualizar y verificar la información del vehículo."
        />
      )}

      {canEnter ? (
        <StepCard
          step={3}
          kicker="Asignación"
          title="Asignar celda"
          aside={
            <p className="text-sm text-muted">
              <span className="text-lg font-bold text-success">{cells.length}</span>{" "}
              celdas disponibles
            </p>
          }
        >
          <p className="mb-3 text-xs text-muted">
            {vehicle!.tipo_vehiculo === "MOTO"
              ? "Selecciona una celda para moto"
              : "Selecciona una celda para carro o camioneta"}
          </p>
          {cells.length === 0 ? (
            <p className="rounded-xl bg-black/20 py-4 text-center text-xs text-warning">
              No hay celdas disponibles para este tipo de vehículo.
            </p>
          ) : (
            <div className="grid max-h-[220px] grid-cols-4 gap-2 overflow-y-auto pr-1 sm:grid-cols-6 lg:grid-cols-12">
              {cells.map((c) => (
                <CellChip
                  key={c.id_celda}
                  code={c.codigo}
                  selected={cell === c.codigo}
                  onSelect={() => setCell(c.codigo)}
                />
              ))}
            </div>
          )}
          <label htmlFor="operator" className="mb-2 mt-6 block text-xs font-bold">
            Operador responsable
          </label>
          <div className="flex gap-3">
            <div className="min-w-0 flex-1">
              <OperatorSelect id="operator" operators={operators} value={operator} onChange={setOperator} />
            </div>
            <PrimaryButton onClick={onRegister} disabled={!cell || operator === null || submitting}>
              {submitting ? "Registrando…" : "Registrar entrada"}
              <ArrowRight size={16} />
            </PrimaryButton>
          </div>
        </StepCard>
      ) : (
        <StepCard
          step={3}
          kicker="Asignación"
          title="Asignar celda"
          disabled
          placeholder="Completa y verifica los pasos anteriores para asignar una celda."
        />
      )}
    </>
  );
}
