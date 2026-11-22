import { AlertCircle, Check, TriangleAlert } from "lucide-react";

const STYLES = {
  success: { Icon: Check, cls: "border-success/40 bg-success/10 text-success", role: "status" },
  error: { Icon: AlertCircle, cls: "border-danger/40 bg-danger/10 text-danger", role: "alert" },
  warning: { Icon: TriangleAlert, cls: "border-warning/40 bg-warning/10 text-warning", role: "status" },
} as const;

export default function Alert({
  kind,
  title,
  detail,
  testId,
  urgent = false,
}: {
  kind: "success" | "error" | "warning";
  title: string;
  detail?: string;
  testId?: string;
  /** Announce as an alert (e.g. a blocking warning) instead of a status. */
  urgent?: boolean;
}) {
  const { Icon, cls, role } = STYLES[kind];
  return (
    <div
      role={urgent ? "alert" : role}
      data-testid={testId}
      className={`mb-4 flex items-start gap-4 rounded-2xl border px-5 py-4 text-sm ${cls}`}
    >
      <Icon size={18} className="mt-0.5 shrink-0" />
      <div>
        <p className="font-bold">{title}</p>
        {detail && <p className="mt-1 opacity-90">{detail}</p>}
      </div>
    </div>
  );
}
