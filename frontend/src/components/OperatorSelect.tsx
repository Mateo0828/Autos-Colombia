import type { Operator } from "@/types/api";

export default function OperatorSelect({
  id,
  operators,
  value,
  onChange,
}: {
  id: string;
  operators: Operator[];
  value: number | null;
  onChange: (id: number | null) => void;
}) {
  return (
    <select
      id={id}
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
      className="h-11 w-full rounded-xl border border-line bg-[#0a1b3d] px-4 text-sm font-bold outline-none focus:border-accent"
    >
      <option value="">Seleccione un operador</option>
      {operators.map((o) => (
        <option key={o.id_operador} value={o.id_operador}>
          {o.nombre}
        </option>
      ))}
    </select>
  );
}
