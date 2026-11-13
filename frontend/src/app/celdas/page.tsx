"use client";

import { useCallback, useEffect, useState } from "react";
import { Search } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { Cell, CellState, CellType } from "@/types/api";
import { useSummary } from "@/components/SummaryContext";
import RoleGate from "@/components/RoleGate";
import PageHeader from "@/components/PageHeader";
import { SecondaryButton, SelectField, TextField } from "@/components/Fields";
import ConfirmDialog from "@/components/ConfirmDialog";
import Alert from "@/components/Alert";

const STATE_LABEL: Record<CellState, string> = {
  DISPONIBLE: "Disponible",
  OCUPADA: "Ocupada",
  FUERA_DE_SERVICIO: "Fuera de servicio",
};
const STATE_STYLE: Record<CellState, string> = {
  DISPONIBLE: "border-success/50 bg-success/10 text-success",
  OCUPADA: "border-warning/50 bg-warning/10 text-warning",
  FUERA_DE_SERVICIO: "border-danger/50 bg-danger/10 text-danger",
};
const TYPE_LABEL: Record<CellType, string> = { CARRO: "Carro", MOTO: "Moto" };

function CellsScreen() {
  const { refresh } = useSummary();
  const [cells, setCells] = useState<Cell[] | null>(null);
  const [estado, setEstado] = useState<CellState | "">("");
  const [tipo, setTipo] = useState<CellType | "">("");
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [pending, setPending] = useState<Cell | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 250);
    return () => clearTimeout(t);
  }, [q]);

  const load = useCallback(async () => {
    try {
      setCells((await api.cells({ estado, tipo, q: debouncedQ })).celdas);
      setLoadError(null);
    } catch (e) {
      setLoadError(errorMessage(e));
    }
  }, [estado, tipo, debouncedQ]);

  useEffect(() => {
    load();
  }, [load]);

  async function onConfirm() {
    if (!pending) return;
    const disabling = pending.estado !== "FUERA_DE_SERVICIO";
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const r = disabling
        ? await api.disableCell(pending.codigo)
        : await api.enableCell(pending.codigo);
      setSuccess(
        r.mensaje ??
          (disabling
            ? `Celda ${pending.codigo} deshabilitada.`
            : `Celda ${pending.codigo} habilitada.`),
      );
    } catch (err) {
      // e.g. 409 «No se puede deshabilitar una celda ocupada.»
      setError(errorMessage(err));
    } finally {
      setBusy(false);
      setPending(null);
      await load();
      refresh();
    }
  }

  const counts = cells
    ? {
        total: cells.length,
        off: cells.filter((c) => c.estado === "FUERA_DE_SERVICIO").length,
      }
    : null;

  return (
    <>
      <PageHeader
        kicker="Administración"
        title="Celdas"
        subtitle="Consulta las celdas del parqueadero y deshabilita las que estén fuera de servicio. Una celda ocupada no se puede deshabilitar."
      />
      {success && <Alert kind="success" title={success} />}
      {error && <Alert kind="error" title={error} />}
      {loadError && <Alert kind="error" title={loadError} />}

      <div className="mb-4 grid gap-4 rounded-2xl border border-line bg-card p-5 md:grid-cols-[1fr_1fr_1fr]">
        <SelectField
          label="Estado"
          value={estado}
          onChange={(e) => setEstado(e.target.value as CellState | "")}
        >
          <option value="">Todos</option>
          <option value="DISPONIBLE">Disponible</option>
          <option value="OCUPADA">Ocupada</option>
          <option value="FUERA_DE_SERVICIO">Fuera de servicio</option>
        </SelectField>
        <SelectField
          label="Tipo"
          value={tipo}
          onChange={(e) => setTipo(e.target.value as CellType | "")}
        >
          <option value="">Todos</option>
          <option value="CARRO">Carro</option>
          <option value="MOTO">Moto</option>
        </SelectField>
        <div className="relative">
          <TextField
            label="Buscar por código"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Ej. C01"
            autoComplete="off"
          />
          <Search size={15} className="pointer-events-none absolute bottom-3.5 right-4 text-muted" />
        </div>
      </div>

      {counts && (
        <p className="mb-4 text-sm text-muted" data-testid="cells-count">
          <span className="text-2xl font-bold text-accent">{counts.total}</span> celdas
          {counts.off > 0 && ` · ${counts.off} fuera de servicio`}
        </p>
      )}

      {!cells && !loadError && <p className="text-sm text-muted">Cargando…</p>}
      {cells && cells.length === 0 && (
        <p className="rounded-2xl border border-line bg-card px-6 py-12 text-center text-sm text-muted">
          Ninguna celda coincide con los filtros.
        </p>
      )}
      {cells && cells.length > 0 && (
        <div className="max-h-[560px] overflow-auto rounded-2xl border border-line bg-card">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead className="sticky top-0 bg-card">
              <tr className="border-b border-line text-[10px] uppercase tracking-widest text-muted">
                {["Código", "Tipo", "Estado", ""].map((h, i) => (
                  <th key={i} className="px-5 py-4 font-bold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cells.map((c) => {
                const off = c.estado === "FUERA_DE_SERVICIO";
                return (
                  <tr
                    key={c.id_celda}
                    data-testid={`cell-row-${c.codigo}`}
                    className="border-b border-line last:border-0"
                  >
                    <td className="px-5 py-3 font-bold">{c.codigo}</td>
                    <td className="px-5 py-3">{TYPE_LABEL[c.tipo_celda]}</td>
                    <td className="px-5 py-3">
                      <span
                        className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-wider ${STATE_STYLE[c.estado]}`}
                      >
                        {STATE_LABEL[c.estado]}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <SecondaryButton
                        onClick={() => setPending(c)}
                        aria-label={`${off ? "Habilitar" : "Deshabilitar"} celda ${c.codigo}`}
                      >
                        {off ? "Habilitar" : "Deshabilitar"}
                      </SecondaryButton>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {pending && (
        <ConfirmDialog
          title={pending.estado === "FUERA_DE_SERVICIO" ? "Habilitar celda" : "Deshabilitar celda"}
          message={
            pending.estado === "FUERA_DE_SERVICIO"
              ? `La celda ${pending.codigo} volverá a estar disponible para nuevas entradas.`
              : `La celda ${pending.codigo} quedará fuera de servicio y no se ofrecerá en nuevas entradas.`
          }
          confirmLabel={pending.estado === "FUERA_DE_SERVICIO" ? "Habilitar" : "Deshabilitar"}
          busy={busy}
          onConfirm={onConfirm}
          onCancel={() => setPending(null)}
        />
      )}
    </>
  );
}

export default function CellsPage() {
  return (
    <RoleGate role="ADMINISTRADOR">
      <CellsScreen />
    </RoleGate>
  );
}
