import { useId } from "react";

export const inputClass =
  "h-11 w-full rounded-xl border border-line bg-[#0a1b3d] px-4 text-sm font-bold outline-none placeholder:font-normal placeholder:text-muted focus:border-accent disabled:opacity-50";

interface BaseProps {
  label: string;
  error?: string | null;
  hint?: string;
}

export function TextField({
  label,
  error,
  hint,
  ...props
}: BaseProps & React.InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-xs font-bold">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        {...props}
        className={`${inputClass} ${error ? "border-danger" : ""}`}
      />
      {error ? (
        <p role="alert" className="mt-1.5 text-xs text-danger">
          {error}
        </p>
      ) : (
        hint && <p className="mt-1.5 text-xs text-muted">{hint}</p>
      )}
    </div>
  );
}

export function SelectField({
  label,
  error,
  hint,
  children,
  ...props
}: BaseProps & React.SelectHTMLAttributes<HTMLSelectElement>) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-xs font-bold">
        {label}
      </label>
      <select
        id={id}
        aria-invalid={error ? true : undefined}
        {...props}
        className={`${inputClass} ${error ? "border-danger" : ""}`}
      >
        {children}
      </select>
      {error ? (
        <p role="alert" className="mt-1.5 text-xs text-danger">
          {error}
        </p>
      ) : (
        hint && <p className="mt-1.5 text-xs text-muted">{hint}</p>
      )}
    </div>
  );
}

export function SecondaryButton({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      {...props}
      className="inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-accent/40 bg-[#0a1b3d]/60 px-5 text-sm font-bold text-accent transition hover:bg-accent/10 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {children}
    </button>
  );
}
