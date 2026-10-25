export default function PageHeader({
  kicker,
  title,
  subtitle,
}: {
  kicker?: string;
  title: string;
  subtitle: string;
}) {
  return (
    <header className="mb-8">
      {kicker && (
        <p className="text-[11px] font-bold uppercase tracking-widest text-accent">
          {kicker}
        </p>
      )}
      <h1 className="mt-2 text-4xl font-medium tracking-tight">{title}</h1>
      <p className="mt-3 text-[15px] text-muted">{subtitle}</p>
    </header>
  );
}
