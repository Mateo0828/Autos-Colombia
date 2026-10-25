export default function InfoGrid({
  items,
}: {
  items: { label: string; value: string }[];
}) {
  return (
    <dl className="grid grid-cols-1 overflow-hidden rounded-xl border border-line sm:grid-cols-3">
      {items.map((it, i) => (
        <div
          key={it.label}
          className={`p-4 ${i >= 3 ? "sm:border-t sm:border-line" : ""} ${i % 3 !== 0 ? "sm:border-l sm:border-line" : ""}`}
        >
          <dt className="text-[11px] text-muted">{it.label}</dt>
          <dd className="mt-1 text-sm font-bold">{it.value}</dd>
        </div>
      ))}
    </dl>
  );
}
