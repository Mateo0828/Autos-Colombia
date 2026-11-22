"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Check, Info, Search, UserPlus, Wallet, X } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import {
  PLATE_ERROR,
  formatDateTime,
  formatDocument,
  isValidPlate,
  monthlyValid,
  normalizePlate,
  vehicleTypeLabel,
} from "@/lib/format";
import type { Cell, EntryValidation, MonthlyInfo } from "@/types/api";
import MonthlyFields from "@/components/MonthlyFields";
import { SecondaryButton } from "@/components/Fields";
import { useSummary } from "@/components/SummaryContext";
import PageHeader from "@/components/PageHeader";
import StepCard from "@/components/StepCard";
import InfoGrid from "@/components/InfoGrid";
import CellChip from "@/components/CellChip";
import { useAuth } from "@/components/AuthContext";
import PrimaryButton from "@/components/PrimaryButton";
import Alert from "@/components/Alert";
import MonthlyBadge from "@/components/MonthlyBadge";

export default function EntryPage() {
  const { refresh } = useSummary();
  const { user } = useAuth();

  const [plate, setPlate] = useState("");
  const [checking, setChecking] = useState(false);
  const [validation, setValidation] = useState<EntryValidation | null>(null);
  // Monthly data, fetched only when the entry is blocked by the monthly fee (mockup m12).
  const [monthly, setMonthly] = useState<MonthlyInfo | null>(null);
  const [cells, setCells] = useState<Cell[]>([]);
  const [cell, setCell] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ title: string; detail: string } | null>(null);

  const vehicle = validation?.vehiculo ?? null;
  const canEnter = validation?.puede_ingresar === true && vehicle !== null;
  // F-06: decided by `codigo_motivo`; the `motivo` text is only displayed, never interpreted.
  const code = validation?.codigo_motivo;
  const blockedByMonthly = code === "SIN_PRIMER_PAGO" || code === "MENSUALIDAD_VENCIDA";

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
    setMonthly(null);
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
      else if (v.vehiculo && (v.codigo_motivo === "SIN_PRIMER_PAGO" || v.codigo_motivo === "MENSUALIDAD_VENCIDA")) {
        try {
          setMonthly(await api.monthly(v.vehiculo.placa));
        } catch {
          // The motivo and the payment link are enough if this extra query fails.
        }
      }
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setChecking(false);
    }
  }

  async function onRegister() {
    if (!vehicle || !cell) return;
    setSubmitting(true);
    setError(null);
    try {
      const r = await api.registerEntry({
        placa: vehicle.placa,
        codigo_celda: cell,
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
        ["Mensualidad vigente", monthlyValid(validation.validaciones)],
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

      {vehicle && validation && blockedByMonthly ? (
        // Blocked by the monthly fee: banner with the server's motivo, monthly data, way to pay (m12).
        <>
          <Alert kind="warning" title={validation.motivo} urgent />
          <StepCard
            step={2}
            kicker="Verificación"
            title={`Vehículo ${vehicle.placa}`}
            aside={<MonthlyBadge state={monthly?.estado_mensualidad ?? vehicle.estado_mensualidad} />}
          >
            {monthly ? (
              <MonthlyFields info={monthly} />
            ) : (
              <InfoGrid
                items={[
                  { label: "Cliente", value: vehicle.cliente.nombre },
                  { label: "Tipo de vehículo", value: vehicleTypeLabel(vehicle.tipo_vehiculo) },
                  { label: "Documento", value: formatDocument(vehicle.cliente.documento) },
                ]}
              />
            )}
            <div className="mt-6 flex justify-end gap-3">
              <SecondaryButton onClick={() => setValidation(null)}>Cancelar</SecondaryButton>
              <Link
                href={`/pagos?placa=${encodeURIComponent(vehicle.placa)}`}
                className="inline-flex h-11 items-center gap-2 rounded-xl bg-accent px-5 text-sm font-bold text-[#0a1b3d] hover:brightness-110"
              >
                <Wallet size={16} />
                {code === "SIN_PRIMER_PAGO" ? "Registrar primer pago" : "Registrar pago de renovación"}
              </Link>
            </div>
          </StepCard>
        </>
      ) : vehicle ? (
        <StepCard
          step={2}
          kicker="Verificación"
          title="Datos del vehículo"
          aside={<MonthlyBadge state={vehicle.estado_mensualidad} />}
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
          {code === "VEHICULO_NO_REGISTRADO" && (
            <Link
              href={`/registro?placa=${encodeURIComponent(normalizePlate(plate))}`}
              className="mt-4 inline-flex h-11 items-center gap-2 rounded-xl border border-accent/40 bg-[#0a1b3d]/60 px-5 text-sm font-bold text-accent hover:bg-accent/10"
            >
              <UserPlus size={16} />
              Registrar cliente y vehículo
            </Link>
          )}
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
          <div className="mt-6 flex items-center justify-between gap-3">
            <p className="text-sm" data-testid="operator-label">
              <span className="text-muted">Operador: </span>
              <strong>{user?.nombre}</strong>
            </p>
            <PrimaryButton onClick={onRegister} disabled={!cell || submitting}>
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
