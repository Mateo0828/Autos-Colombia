type Tone = "default" | "success" | "warning";

const TONES: Record<Tone, string> = {
  default: "text-foreground",
  success: "text-success",
  warning: "text-warning",
};

export default function StatCard({
  label,
  value,
  note,
  tone = "default",
  large = false,
}: {
  label: string;
  value: number | string;
  note?: string;
  tone?: Tone;
  large?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border border-line bg-card ${large ? "p-6" : "p-4"}`}
    >
      <p className="text-xs text-muted">{label}</p>
      <p
        className={`mt-2 font-bold ${TONES[tone]} ${large ? "text-4xl" : "text-3xl"}`}
      >
        {value}
      </p>
      {note && <p className="mt-3 text-xs text-muted">{note}</p>}
    </div>
  );
}
