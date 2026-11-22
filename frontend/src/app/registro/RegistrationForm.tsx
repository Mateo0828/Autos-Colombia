"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Save } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { isValidPlate, normalizePlate } from "@/lib/format";
import { validateClient, validateVehicle, type FieldErrors } from "@/lib/validation";
import type { VehicleType } from "@/types/api";
import { useSummary } from "@/components/SummaryContext";
import PageHeader from "@/components/PageHeader";
import StepCard from "@/components/StepCard";
import { SelectField, TextField } from "@/components/Fields";
import PrimaryButton from "@/components/PrimaryButton";
import Alert from "@/components/Alert";

export default function RegistrationForm() {
  const { refresh } = useSummary();
  const initialPlate = normalizePlate(useSearchParams().get("placa") ?? "");

  const [documento, setDocumento] = useState("");
  const [nombre, setNombre] = useState("");
  const [placa, setPlaca] = useState(isValidPlate(initialPlate) ? initialPlate : "");
  const [marca, setMarca] = useState("");
  const [color, setColor] = useState("");
  const [tipo, setTipo] = useState<VehicleType | "">("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ title: string; plate: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSuccess(null);
    setError(null);
    const plate = normalizePlate(placa);
    const next: FieldErrors = {
      ...validateClient({ documento, nombre }),
      ...validateVehicle({ placa: plate, marca, color, tipo }),
    };
    setErrors(next);
    if (Object.keys(next).length > 0 || tipo === "") return;
    setSubmitting(true);
    try {
      const r = await api.register({
        documento: documento.trim(),
        nombre: nombre.trim(),
        placa: plate,
        marca: marca.trim(),
        color: color.trim(),
        tipo_vehiculo: tipo,
      });
      setSuccess({ title: r.mensaje ?? "Cliente y vehículo registrados correctamente.", plate });
      setDocumento("");
      setNombre("");
      setPlaca("");
      setMarca("");
      setColor("");
      setTipo("");
      refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        kicker="Control de acceso"
        title="Registrar cliente y vehículo"
        subtitle="Completa los datos para poder continuar con el primer pago de la mensualidad."
      />
      {!success && initialPlate && isValidPlate(initialPlate) && (
        <Alert kind="warning" title={`La placa ${initialPlate} no se encuentra registrada.`} />
      )}
      {success && (
        <Alert
          kind="success"
          title={success.title}
          detail={`Placa ${success.plate}. La mensualidad queda INACTIVA hasta registrar el primer pago.`}
        />
      )}
      {success && (
        <p className="-mt-2 mb-4 flex flex-wrap items-center gap-x-6 gap-y-2">
          <Link
            href={`/pagos?placa=${encodeURIComponent(success.plate)}`}
            className="inline-flex items-center gap-2 text-sm font-bold text-accent hover:underline"
          >
            Registrar primer pago <ArrowRight size={14} />
          </Link>
          <Link href="/entrada" className="text-sm text-muted hover:text-foreground hover:underline">
            Volver a Entrada
          </Link>
        </p>
      )}
      {error && <Alert kind="error" title={error} />}

      <form onSubmit={onSubmit} noValidate>
        <StepCard step={1} kicker="Primer paso" title="Datos del cliente">
          <div className="grid gap-5 md:grid-cols-2">
            <TextField
              label="Documento"
              value={documento}
              onChange={(e) => setDocumento(e.target.value)}
              maxLength={20}
              autoComplete="off"
              placeholder="Ej. 1012345678"
              error={errors.documento}
            />
            <TextField
              label="Nombre completo"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              maxLength={100}
              autoComplete="off"
              error={errors.nombre}
            />
          </div>
          <p className="mt-3 text-xs text-muted">
            Si el documento ya existe, el vehículo se asocia al cliente registrado.
          </p>
        </StepCard>
        <StepCard step={2} kicker="Segundo paso" title="Datos del vehículo">
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            <TextField
              label="Placa"
              value={placa}
              onChange={(e) => setPlaca(e.target.value.toUpperCase())}
              maxLength={10}
              autoComplete="off"
              placeholder="Ej. ABC123"
              error={errors.placa}
            />
            <TextField
              label="Marca"
              value={marca}
              onChange={(e) => setMarca(e.target.value)}
              maxLength={50}
              autoComplete="off"
              error={errors.marca}
            />
            <TextField
              label="Color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              maxLength={30}
              autoComplete="off"
              error={errors.color}
            />
            <SelectField
              label="Tipo de vehículo"
              value={tipo}
              onChange={(e) => setTipo(e.target.value as VehicleType | "")}
              error={errors.tipo}
            >
              <option value="">Seleccione un tipo</option>
              <option value="MOTO">Moto</option>
              <option value="AUTOMOVIL">Automóvil</option>
              <option value="CAMIONETA">Camioneta</option>
            </SelectField>
          </div>
          <p className="mt-4 text-xs text-muted">
            El vehículo queda sin cobertura (INACTIVA) hasta registrar su primer pago. Solo el
            administrador podrá modificar estos datos después del registro.
          </p>
          <div className="mt-6 flex justify-end gap-3">
            <Link
              href="/entrada"
              className="inline-flex h-11 items-center rounded-xl border border-accent/40 bg-[#0a1b3d]/60 px-5 text-sm font-bold text-accent hover:bg-accent/10"
            >
              Cancelar
            </Link>
            <PrimaryButton type="submit" disabled={submitting}>
              <Save size={16} />
              {submitting ? "Registrando…" : "Registrar cliente y vehículo"}
            </PrimaryButton>
          </div>
        </StepCard>
      </form>
    </>
  );
}
