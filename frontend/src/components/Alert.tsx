import { AlertCircle, Check } from "lucide-react";

export default function Alert({
  kind,
  title,
  detail,
}: {
  kind: "success" | "error";
  title: string;
  detail?: string;
}) {
  const ok = kind === "success";
  const Icon = ok ? Check : AlertCircle;
  return (
    <div
      role={ok ? "status" : "alert"}
      className={`mb-4 flex items-start gap-4 rounded-2xl border px-5 py-4 text-sm ${
        ok
          ? "border-success/40 bg-success/10 text-success"
          : "border-danger/40 bg-danger/10 text-danger"
      }`}
    >
      <Icon size={18} className="mt-0.5 shrink-0" />
      <div>
        <p className="font-bold">{title}</p>
        {detail && <p className="mt-1 opacity-90">{detail}</p>}
      </div>
    </div>
  );
}
