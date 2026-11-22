/** Read-only monthly state (D-31): green «Mensualidad ACTIVA», red «Mensualidad INACTIVA». Never editable. */
export default function MonthlyBadge({ state, suffix = "" }: { state: string; suffix?: string }) {
  const active = state === "ACTIVA";
  return (
    <span
      data-testid="monthly-state"
      className={`rounded-full border px-3 py-1 text-[11px] font-bold ${
        active
          ? "border-success/50 bg-success/10 text-success"
          : "border-danger/50 bg-danger/10 text-danger"
      }`}
    >
      Mensualidad {state}
      {suffix}
    </span>
  );
}
