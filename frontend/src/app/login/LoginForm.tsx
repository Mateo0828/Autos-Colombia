"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { LogIn } from "lucide-react";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/components/AuthContext";
import { TextField } from "@/components/Fields";
import PrimaryButton from "@/components/PrimaryButton";
import Alert from "@/components/Alert";

export default function LoginForm() {
  const { login } = useAuth();
  const expired = useSearchParams().get("expirada") === "1";
  const [usuario, setUsuario] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ usuario?: string; password?: string }>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const next: typeof errors = {};
    if (!usuario.trim()) next.usuario = "Ingresa tu usuario.";
    if (!password) next.password = "Ingresa tu contraseña.";
    setErrors(next);
    setError(null);
    if (Object.keys(next).length > 0) return;
    setSubmitting(true);
    try {
      await login(usuario.trim(), password);
      // AppShell redirects to /entrada once the user is set.
    } catch (err) {
      setError(errorMessage(err));
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(ellipse_at_top,#12326a_0%,#0a1b3d_45%)] px-4">
      <div className="w-full max-w-[420px]">
        <div className="mb-8 text-center">
          <p className="text-4xl font-extrabold text-accent">AC</p>
          <h1 className="mt-3 text-2xl font-medium">Autos Colombia</h1>
          <p className="mt-2 text-sm text-muted">Inicia sesión para continuar</p>
        </div>
        {expired && !error && (
          <Alert kind="error" title="Tu sesión terminó. Inicia sesión de nuevo." />
        )}
        {error && <Alert kind="error" title={error} />}
        <form
          onSubmit={onSubmit}
          noValidate
          className="space-y-5 rounded-2xl border border-line bg-card p-6"
        >
          <TextField
            label="Usuario"
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            autoComplete="username"
            autoFocus
            error={errors.usuario}
          />
          <TextField
            label="Contraseña"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            error={errors.password}
          />
          <PrimaryButton type="submit" disabled={submitting} style={{ width: "100%" }}>
            <LogIn size={16} />
            {submitting ? "Ingresando…" : "Iniciar sesión"}
          </PrimaryButton>
        </form>
      </div>
    </div>
  );
}
