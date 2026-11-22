import type { MonthlyInfo } from "@/types/api";
import { formatDate, formatMoney, vehicleTypeLabel } from "@/lib/format";
import InfoGrid from "./InfoGrid";

/** Monthly data block, in the order of mockups m8/m12. Everything comes from the API. */
export default function MonthlyFields({ info }: { info: MonthlyInfo }) {
  return (
    <InfoGrid
      items={[
        { label: "Cliente", value: info.cliente.nombre },
        { label: "Tipo de vehículo", value: vehicleTypeLabel(info.vehiculo.tipo_vehiculo) },
        { label: "Tarifa mensual", value: formatMoney(info.tarifa) },
        { label: "Fecha de inicio", value: formatDate(info.fecha_inicio) },
        { label: "Fecha de corte (vencimiento)", value: formatDate(info.fecha_corte) },
        { label: "Día de corte", value: info.dia_corte === null ? "—" : String(info.dia_corte) },
        { label: "Pagos registrados", value: String(info.num_pagos) },
      ]}
    />
  );
}
