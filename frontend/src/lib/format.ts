import type { VehicleType } from "@/types/api";

const TYPE_LABELS: Record<VehicleType, string> = {
  MOTO: "Moto",
  AUTOMOVIL: "Automóvil",
  CAMIONETA: "Camioneta",
};

export function vehicleTypeLabel(t: VehicleType): string {
  return TYPE_LABELS[t] ?? t;
}

export function formatDocument(doc: string): string {
  return doc.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

// Server dates are ISO 8601 without timezone: shown as-is, no zone conversion.
export function formatDateTime(iso: string): string {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  if (!m) return iso;
  const [, y, mo, d, h, mi] = m;
  const hour = Number(h);
  const suffix = hour >= 12 ? "p. m." : "a. m.";
  const h12 = hour % 12 === 0 ? 12 : hour % 12;
  const time = `${h12}:${mi} ${suffix}`;
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  return `${y}-${mo}-${d}` === today ? `Hoy, ${time}` : `${d}/${mo}/${y}, ${time}`;
}

export const PLATE_ERROR =
  "La placa solo puede contener letras y números (máximo 10).";

export function normalizePlate(value: string): string {
  return value.trim().toUpperCase();
}

// D-13: letters and digits only, 1 to 10 characters.
export function isValidPlate(plate: string): boolean {
  return /^[A-Z0-9]{1,10}$/.test(plate);
}

export function percent(part: number, total: number): number {
  return total > 0 ? Math.round((part / total) * 1000) / 10 : 0;
}
