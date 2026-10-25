export default function StepCard({
  step,
  kicker,
  title,
  disabled = false,
  placeholder,
  aside,
  children,
}: {
  step: number;
  kicker: string;
  title: string;
  disabled?: boolean;
  placeholder?: string;
  aside?: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <section
      className={`mb-4 rounded-2xl border p-6 ${
        disabled ? "border-dashed border-line bg-card/30" : "border-line bg-card"
      }`}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span
            className={`flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold ${
              disabled ? "bg-white/10 text-muted" : "bg-accent text-[#0a1b3d]"
            }`}
          >
            {step}
          </span>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-accent">
              {kicker}
            </p>
            <h2 className="text-lg">{title}</h2>
          </div>
        </div>
        {aside}
      </div>
      {disabled ? (
        <p className="mt-5 rounded-xl bg-black/20 py-4 text-center text-xs text-muted">
          {placeholder}
        </p>
      ) : (
        <div className="mt-5">{children}</div>
      )}
    </section>
  );
}
