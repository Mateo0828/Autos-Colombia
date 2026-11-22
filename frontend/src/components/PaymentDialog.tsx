"use client";

import { useState } from "react";
import type { MonthlyInfo, NextPayment } from "@/types/api";
import { formatDate, formatMoney } from "@/lib/format";
import PrimaryButton from "./PrimaryButton";
import { SecondaryButton, inputClass } from "./Fields";

/**
 * Confirmation window for a payment (mockups m9/m10). Everything shown comes from the server's
 * projection (`proximo_pago`): value, new cut-off date, resulting state and warning. The amount is
 * read-only and never submitted. When the date changes the screen asks the server again.
 */
export default function PaymentDialog({
  info,
  today,
  projection,
  projecting,
  busy,
  error,
  onDateChange,
  onConfirm,
  onCancel,
}: {
  info: MonthlyInfo;
  /** Server's "today" (`proximo_pago.fecha_pago` of the first query): default date and upper bound. */
  today: string;
  projection: NextPayment;
  projecting: boolean;
  busy: boolean;
  error: string | null;
  onDateChange: (date: string) => void;
  onConfirm: (fechaPago: string) => void;
  onCancel: () => void;
}) {
  const [date, setDate] = useState(today);
  const [dateError, setDateError] = useState<string | null>(null);

  const first = projection.tipo === "PRIMER_PAGO";
  // A cut-off date later than today means this payment is made in advance.
  const advance = info.fecha_corte !== null && info.fecha_corte > today;
  // The projection on screen must be the one for the date in the field.
  const stale = projecting || projection.fecha_pago !== date;
  const title = first ? "Confirmar pago inicial" : "Confirmar pago de renovación";

  function changeDate(value: string) {
    setDate(value);
    if (!value) {
      setDateError("Indica la fecha del pago.");
      return;
    }
    if (value > today) {
      setDateError("La fecha de pago no puede ser futura.");
      return;
    }
    setDateError(null);
    onDateChange(value);
  }

  function submit() {
    if (dateError || !date || stale) return;
    onConfirm(date);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-2xl border border-line bg-card p-6 shadow-2xl"
      >
        <p className="text-[10px] font-bold uppercase tracking-widest text-accent">
          {first ? "Primer pago" : "Renovación"} · {info.vehiculo.placa}
        </p>
        <h2 className="mt-1 text-xl font-bold">{title}</h2>

        {error && (
          <p role="alert" className="mt-4 rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-xs font-bold text-danger">
            {error}
          </p>
        )}

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="pay-value" className="mb-2 block text-xs font-bold">
              Valor a pagar
            </label>
            <input
              id="pay-value"
              value={formatMoney(projection.valor)}
              readOnly
              aria-readonly="true"
              className={`${inputClass} text-muted`}
            />
          </div>
          <div>
            <label htmlFor="pay-date" className="mb-2 block text-xs font-bold">
              Fecha del pago
            </label>
            <input
              id="pay-date"
              type="date"
              value={date}
              max={today}
              onChange={(e) => changeDate(e.target.value)}
              aria-invalid={dateError ? true : undefined}
              className={`${inputClass} ${dateError ? "border-danger" : ""}`}
            />
            {dateError && (
              <p role="alert" className="mt-1.5 text-xs text-danger">
                {dateError}
              </p>
            )}
          </div>
        </div>

        {advance && (
          <p
            data-testid="advance-notice"
            className="mt-4 rounded-xl border border-accent/40 bg-accent/10 px-4 py-3 text-xs"
          >
            Pago anticipado: se conservan los días ya pagados.
          </p>
        )}

        <div
          data-testid="payment-projection"
          aria-busy={stale}
          className={`mt-4 space-y-1 rounded-xl border border-line bg-black/20 px-4 py-3 text-sm ${stale ? "opacity-60" : ""}`}
        >
          {first ? (
            <p>
              Inicio de la mensualidad: <strong>{formatDate(projection.periodo_inicio)}</strong>
            </p>
          ) : (
            <p>
              Fecha de corte actual: <strong>{formatDate(info.fecha_corte)}</strong>
            </p>
          )}
          <p>
            Nueva fecha de corte: <strong data-testid="next-cutoff">{formatDate(projection.periodo_fin)}</strong>
          </p>
          <p>
            Día de corte:{" "}
            <strong data-testid="cutoff-day">
              {info.dia_corte ?? "se define con el primer pago"}
            </strong>
          </p>
          <p>
            Estado resultante:{" "}
            <strong
              data-testid="resulting-state"
              className={projection.estado_resultante === "ACTIVA" ? "text-success" : "text-danger"}
            >
              {projection.estado_resultante}
            </strong>
          </p>
        </div>

        {projection.advertencia && (
          <p
            role="status"
            data-testid="projection-warning"
            className="mt-4 rounded-xl border border-warning/40 bg-warning/10 px-4 py-3 text-xs text-warning"
          >
            {projection.advertencia}
          </p>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <SecondaryButton onClick={onCancel} disabled={busy}>
            Cancelar
          </SecondaryButton>
          <PrimaryButton onClick={submit} disabled={busy || stale || dateError !== null}>
            {busy ? "Registrando…" : projecting ? "Calculando…" : "Confirmar pago"}
          </PrimaryButton>
        </div>
      </div>
    </div>
  );
}
