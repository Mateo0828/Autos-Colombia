import Link from "next/link";
import type { ActiveStay } from "@/types/api";
import { formatDateTime, vehicleTypeLabel } from "@/lib/format";

const HEADERS = [
  "Placa",
  "Marca / Color",
  "Tipo",
  "Celda",
  "Fecha y hora de entrada",
  "Operador de entrada",
  "",
];

export default function VehiclesTable({ stays }: { stays: ActiveStay[] }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-line bg-card">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead>
          <tr className="border-b border-line text-[10px] uppercase tracking-widest text-muted">
            {HEADERS.map((h, i) => (
              <th key={i} className="px-5 py-4 font-bold">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {stays.map((s) => (
            <tr key={s.id_estancia} className="border-b border-line last:border-0">
              <td className="px-5 py-5 font-bold">{s.vehiculo.placa}</td>
              <td className="px-5 py-5">
                <p>{s.vehiculo.marca}</p>
                <p className="text-[11px] text-muted">{s.vehiculo.color}</p>
              </td>
              <td className="px-5 py-5">{vehicleTypeLabel(s.vehiculo.tipo_vehiculo)}</td>
              <td className="px-5 py-5">
                <span className="rounded-md border border-accent/40 bg-accent/10 px-2 py-1 text-xs font-bold text-accent">
                  {s.celda.codigo}
                </span>
              </td>
              <td className="px-5 py-5">{formatDateTime(s.fecha_hora_entrada)}</td>
              <td className="px-5 py-5">{s.operador_entrada.nombre}</td>
              <td className="px-5 py-5">
                <Link
                  href={`/salida?placa=${encodeURIComponent(s.vehiculo.placa)}`}
                  className="inline-block rounded-xl border border-accent/40 bg-[#0a1b3d]/60 px-4 py-2.5 text-xs font-bold text-accent hover:bg-accent/10"
                >
                  Registrar salida
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
