export default function PrimaryButton({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-accent px-5 text-sm font-bold text-[#0a1b3d] transition hover:brightness-110 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-muted disabled:hover:brightness-100"
    >
      {children}
    </button>
  );
}
