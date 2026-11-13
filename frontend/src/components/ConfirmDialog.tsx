"use client";

import PrimaryButton from "./PrimaryButton";
import { SecondaryButton } from "./Fields";

export default function ConfirmDialog({
  title,
  message,
  confirmLabel,
  busy = false,
  onConfirm,
  onCancel,
}: {
  title: string;
  message: string;
  confirmLabel: string;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="w-full max-w-md rounded-2xl border border-line bg-card p-6 shadow-2xl"
      >
        <h2 className="text-lg font-bold">{title}</h2>
        <p className="mt-3 text-sm text-muted">{message}</p>
        <div className="mt-6 flex justify-end gap-3">
          <SecondaryButton onClick={onCancel} disabled={busy}>
            Cancelar
          </SecondaryButton>
          <PrimaryButton onClick={onConfirm} disabled={busy}>
            {busy ? "Procesando…" : confirmLabel}
          </PrimaryButton>
        </div>
      </div>
    </div>
  );
}
