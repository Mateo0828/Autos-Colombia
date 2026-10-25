export default function ProgressBar({
  label,
  available,
  total,
}: {
  label: string;
  available: number;
  total: number;
}) {
  const pct = total > 0 ? (available / total) * 100 : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted">{label}</span>
        <span className="font-bold">
          {available} / {total} disponibles
        </span>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-accent"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
