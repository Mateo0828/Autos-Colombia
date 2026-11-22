"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { History, Info, Search, Wallet } from "lucide-react";
import { ApiRequestError, api, errorMessage } from "@/lib/api";
import { PLATE_ERROR, formatDate, formatMoney, isValidPlate, normalizePlate } from "@/lib/format";
import type { MonthlyInfo, NextPayment, PaymentHistory, PaymentResult } from "@/types/api";
import PageHeader from "@/components/PageHeader";
import StepCard from "@/components/StepCard";
import MonthlyFields from "@/components/MonthlyFields";
import PrimaryButton from "@/components/PrimaryButton";
import { SecondaryButton } from "@/components/Fields";
import Alert from "@/components/Alert";
import MonthlyBadge from "@/components/MonthlyBadge";
import PaymentDialog from "@/components/PaymentDialog";
import PaymentHistoryTable from "@/components/PaymentHistoryTable";

export default function PaymentsScreen() {
  const initialPlate = normalizePlate(useSearchParams().get("placa") ?? "");

  const [plate, setPlate] = useState(isValidPlate(initialPlate) ? initialPlate : "");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<MonthlyInfo | null>(null);
  const [result, setResult] = useState<PaymentResult | null>(null);

  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState<PaymentHistory | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogError, setDialogError] = useState<string | null>(null);
  // Server projection for the date chosen in the dialog (GET ?fecha_pago=). Nothing is computed here.
  const [projection, setProjection] = useState<NextPayment | null>(null);
  const [projecting, setProjecting] = useState(false);
  const projSeq = useRef(0);
  // The server's "today": `proximo_pago.fecha_pago` of a query made without fecha_pago.
  const serverToday = info?.proximo_pago.fecha_pago ?? "";
  const [paying, setPaying] = useState(false);
  // Synchronous guard against a double click sending two payments (D-33).
  const payingRef = useRef(false);

  async function loadHistory(p: string) {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      setHistory(await api.payments(p));
    } catch (err) {
      setHistory(null);
      setHistoryError(errorMessage(err));
    } finally {
      setHistoryLoading(false);
    }
  }

  /** Query the monthly state. `fresh` = new search (clears result/history); otherwise a reload. */
  async function consult(raw: string, fresh: boolean) {
    const value = normalizePlate(raw);
    if (!value) return;
    // A reload after a 409 must keep the message that explains why it happened.
    if (fresh) {
      setError(null);
      setResult(null);
      setInfo(null);
      setHistoryOpen(false);
      setHistory(null);
      setHistoryError(null);
    }
    if (!isValidPlate(value)) {
      setError(PLATE_ERROR);
      return;
    }
    setSearching(true);
    try {
      const r = await api.monthly(value);
      setInfo(r);
      setProjection(r.proximo_pago);
    } catch (err) {
      setInfo(null);
      setError(errorMessage(err));
    } finally {
      setSearching(false);
    }
  }

  // Arrived from Entrada or Registro with ?placa=: consult once.
  const autoRan = useRef(false);
  useEffect(() => {
    if (autoRan.current || !initialPlate || !isValidPlate(initialPlate)) return;
    autoRan.current = true;
    void consult(initialPlate, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onToggleHistory() {
    if (!info) return;
    if (historyOpen) {
      setHistoryOpen(false);
      return;
    }
    setHistoryOpen(true);
    await loadHistory(info.vehiculo.placa);
  }

  /** The date changed in the dialog: ask the server again for that date (valor, corte, estado, advertencia). */
  async function onDateChange(date: string) {
    if (!info) return;
    setDialogError(null);
    if (date === serverToday) {
      projSeq.current++;
      setProjection(info.proximo_pago);
      setProjecting(false);
      return;
    }
    const seq = ++projSeq.current;
    setProjecting(true);
    try {
      const r = await api.monthly(info.vehiculo.placa, date);
      if (seq === projSeq.current) setProjection(r.proximo_pago);
    } catch (err) {
      if (seq === projSeq.current) setDialogError(errorMessage(err));
    } finally {
      if (seq === projSeq.current) setProjecting(false);
    }
  }

  async function onConfirm(fechaPago: string) {
    if (!info || !projection || projection.fecha_pago !== fechaPago || payingRef.current) return;
    payingRef.current = true;
    setPaying(true);
    setDialogError(null);
    setError(null);
    const p = info.vehiculo.placa;
    try {
      const r = await api.registerPayment({
        placa: p,
        fecha_pago: fechaPago,
        // D-33/F-06: exactly what the server projected for THIS date; null only for the first payment. No `valor`.
        corte_esperado: projection.corte_esperado,
      });
      setResult(r);
      setDialogOpen(false);
      await consult(p, false);
      if (historyOpen) await loadHistory(p);
    } catch (err) {
      const status = err instanceof ApiRequestError ? err.status : null;
      if (status === 422) {
        setDialogError(errorMessage(err)); // fix the data and retry
      } else {
        // 409 (already updated), 404, connection: show it and reload what the server now says.
        setDialogOpen(false);
        setResult(null);
        setError(errorMessage(err));
        if (status === 409) {
          await consult(p, false);
          if (historyOpen) await loadHistory(p);
        }
      }
    } finally {
      payingRef.current = false;
      setPaying(false);
    }
  }

  const first = info?.num_pagos === 0;

  return (
    <>
      <PageHeader
        kicker="Gestión de pagos"
        title="Consultar mensualidad"
        subtitle="Busca un vehículo por su placa para ver su tarifa, estado y fecha de corte. Cada pago amplía la mensualidad un mes calendario; el valor lo calcula el sistema según el tipo de vehículo."
      />

      {error && <Alert kind="error" title={error} />}
      {result && (
        <div data-testid="payment-result">
          <Alert
            kind="success"
            title="Pago registrado correctamente."
            detail={`Valor ${formatMoney(result.pago.valor)} · Período ${formatDate(result.pago.periodo_inicio)} al ${formatDate(result.pago.periodo_fin)} · Nueva fecha de corte ${formatDate(result.mensualidad.fecha_corte)} · Estado ${result.mensualidad.estado_mensualidad} · Registrado por ${result.pago.registrado_por.nombre}`}
          />
          {result.advertencia && (
            <Alert kind="warning" title="Advertencia" detail={result.advertencia} testId="payment-warning" />
          )}
        </div>
      )}

      <StepCard step={1} kicker="Búsqueda" title="Buscar vehículo">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void consult(plate, true);
          }}
        >
          <label htmlFor="pay-plate" className="mb-2 block text-xs font-bold">
            Placa del vehículo
          </label>
          <div className="flex gap-3">
            <input
              id="pay-plate"
              value={plate}
              onChange={(e) => setPlate(e.target.value.toUpperCase())}
              placeholder="Ej. ABC123"
              autoComplete="off"
              className="h-11 min-w-0 flex-1 rounded-xl border border-line bg-[#0a1b3d] px-4 text-sm font-bold uppercase outline-none placeholder:font-normal placeholder:text-muted focus:border-accent"
            />
            <PrimaryButton type="submit" disabled={!plate.trim() || searching}>
              <Search size={16} />
              {searching ? "Consultando…" : "Consultar"}
            </PrimaryButton>
          </div>
        </form>
      </StepCard>

      {info ? (
        <StepCard
          step={2}
          kicker="Estado"
          title={`Vehículo ${info.vehiculo.placa}`}
          aside={<MonthlyBadge state={info.estado_mensualidad} />}
        >
          <div data-testid="monthly-card">
            <MonthlyFields info={info} />
          </div>
          {first && (
            <p className="mt-4 flex items-center gap-3 rounded-xl border border-warning/40 bg-warning/10 px-4 py-3 text-xs text-warning">
              <Info size={15} className="shrink-0" />
              Este vehículo aún no tiene pagos: no podrá ingresar hasta registrar el primer pago.
            </p>
          )}
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
            <SecondaryButton onClick={onToggleHistory} aria-expanded={historyOpen}>
              <History size={16} />
              {historyOpen ? "Ocultar historial" : "Ver historial de pagos"}
            </SecondaryButton>
            <PrimaryButton
              onClick={() => {
                setDialogError(null);
                projSeq.current++;
                setProjecting(false);
                setProjection(info.proximo_pago);
                setDialogOpen(true);
              }}
              disabled={searching}
            >
              <Wallet size={16} />
              {first ? "Registrar primer pago" : "Renovar mensualidad"}
            </PrimaryButton>
          </div>
        </StepCard>
      ) : (
        <StepCard
          step={2}
          kicker="Estado"
          title="Mensualidad del vehículo"
          disabled
          placeholder="Consulta una placa para ver su mensualidad, sus fechas y registrar un pago."
        />
      )}

      {info && historyOpen && (
        <StepCard step={3} kicker="Historial" title="Pagos registrados">
          {historyLoading ? (
            <p className="py-4 text-center text-xs text-muted">Cargando historial…</p>
          ) : historyError ? (
            <p role="alert" className="text-sm font-bold text-danger">
              {historyError}
            </p>
          ) : history ? (
            <PaymentHistoryTable payments={history.pagos} total={history.cantidad} />
          ) : null}
        </StepCard>
      )}

      {info && dialogOpen && projection && (
        <PaymentDialog
          info={info}
          today={serverToday}
          projection={projection}
          projecting={projecting}
          onDateChange={onDateChange}
          busy={paying}
          error={dialogError}
          onConfirm={onConfirm}
          onCancel={() => setDialogOpen(false)}
        />
      )}
    </>
  );
}
