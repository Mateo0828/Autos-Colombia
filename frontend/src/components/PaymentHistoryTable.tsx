import type { PaymentHistoryItem } from "@/types/api";
import { formatDate, formatMoney } from "@/lib/format";

const HEADERS = ["Fecha de pago", "Valor", "Período cubierto", "Registrado por"];

/** Read-only: no edit or delete actions (payments are immutable, D-32). Order comes from the server. */
export default function PaymentHistoryTable({
  payments,
  total,
}: {
  payments: PaymentHistoryItem[];
  total: number;
}) {
  if (payments.length === 0) {
    return (
      <p
        data-testid="history-empty"
        className="rounded-xl bg-black/20 py-4 text-center text-xs text-muted"
      >
        Sin pagos registrados.
      </p>
    );
  }
  return (
    <>
      <div className="overflow-x-auto rounded-xl border border-line">
        <table data-testid="history-table" className="w-full min-w-[560px] text-left text-sm">
          <thead>
            <tr className="border-b border-line text-[10px] uppercase tracking-widest text-muted">
              {HEADERS.map((h) => (
                <th key={h} className="px-4 py-3 font-bold">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {payments.map((p, i) => (
              <tr key={p.id_pago ?? `${p.periodo_inicio}-${i}`} className="border-b border-line last:border-0">
                <td className="px-4 py-3">{formatDate(p.fecha_pago)}</td>
                <td className="px-4 py-3 font-bold">{formatMoney(p.valor)}</td>
                <td className="px-4 py-3">
                  {formatDate(p.periodo_inicio)} – {formatDate(p.periodo_fin)}
                </td>
                <td className="px-4 py-3">{p.registrado_por.nombre}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p data-testid="history-footer" className="mt-3 text-[11px] text-muted">
        Mostrando {payments.length} de {total} pagos · ordenados del más reciente al más antiguo
      </p>
    </>
  );
}
