"use client";

import { useState } from "react";
import { Save, Search } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { PLATE_ERROR, isValidPlate, normalizePlate } from "@/lib/format";
import { validateClient, validateVehicle, type FieldErrors } from "@/lib/validation";
import type { ClientDetail, VehicleType } from "@/types/api";
import RoleGate from "@/components/RoleGate";
import PageHeader from "@/components/PageHeader";
import StepCard from "@/components/StepCard";
import { SelectField, TextField } from "@/components/Fields";
import PrimaryButton from "@/components/PrimaryButton";
import Alert from "@/components/Alert";

type VehicleRow = ClientDetail["vehiculos"][number];

function VehicleEditor({
  vehicle,
  highlighted,
  onSaved,
}: {
  vehicle: VehicleRow;
  highlighted: boolean;
  onSaved: (msg: string) => void;
}) {
  const [marca, setMarca] = useState(vehicle.marca);
  const [color, setColor] = useState(vehicle.color);
  const [tipo, setTipo] = useState<VehicleType | "">(vehicle.tipo_vehiculo);
  const [estadoMens, setEstadoMens] = useState<"ACTIVA" | "INACTIVA">(
    vehicle.estado_mensualidad === "INACTIVA" ? "INACTIVA" : "ACTIVA",
  );
  // D-26: the plate is immutable; it is shown but never sent.
  const placa = vehicle.placa;
  const [errors, setErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const next = validateVehicle({ placa, marca, color, tipo });
    setErrors(next);
    if (Object.keys(next).length > 0 || tipo === "") return;
    setSaving(true);
    try {
      const r = await api.updateVehicle(placa, {
        marca: marca.trim(),
        color: color.trim(),
        tipo_vehiculo: tipo,
        estado_mensualidad: estadoMens,
      });
      onSaved(r.mensaje ?? `Vehículo ${placa} actualizado correctamente.`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      noValidate
      aria-label={`Vehículo ${placa}`}
      className={`rounded-xl border p-5 ${highlighted ? "border-accent/50" : "border-line"}`}
    >
      {error && <Alert kind="error" title={error} />}
      <div className="grid gap-5 md:grid-cols-2">
        <TextField
          label="Placa"
          value={placa}
          readOnly
          aria-readonly="true"
          autoComplete="off"
          error={errors.placa}
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
      </div>
      <div className="mt-5 flex items-center justify-between">
        <label className="flex items-center gap-2 text-xs text-muted">
          Mensualidad
          <select
            value={estadoMens}
            onChange={(e) => setEstadoMens(e.target.value as "ACTIVA" | "INACTIVA")}
            className="rounded-lg border border-line bg-card px-2 py-1 text-sm text-white"
          >
            <option value="ACTIVA">ACTIVA</option>
            <option value="INACTIVA">INACTIVA</option>
          </select>
        </label>
        <PrimaryButton type="submit" disabled={saving}>
          <Save size={16} />
          {saving ? "Guardando…" : "Guardar vehículo"}
        </PrimaryButton>
      </div>
    </form>
  );
}

function ClientsScreen() {
  const [plate, setPlate] = useState("");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [client, setClient] = useState<ClientDetail | null>(null);
  const [searched, setSearched] = useState("");

  const [documento, setDocumento] = useState("");
  const [nombre, setNombre] = useState("");
  const [clientErrors, setClientErrors] = useState<FieldErrors>({});
  const [clientError, setClientError] = useState<string | null>(null);
  const [savingClient, setSavingClient] = useState(false);

  async function onSearch(e: React.FormEvent) {
    e.preventDefault();
    const value = normalizePlate(plate);
    setError(null);
    setSuccess(null);
    setClient(null);
    if (!value) return;
    if (!isValidPlate(value)) {
      setError(PLATE_ERROR);
      return;
    }
    setSearching(true);
    try {
      const v = await api.validateEntry(value);
      if (!v.vehiculo) {
        setError("El vehículo no se encuentra registrado.");
        return;
      }
      const r = await api.client(v.vehiculo.cliente.id_cliente);
      setClient(r.cliente);
      setSearched(value);
      setDocumento(r.cliente.documento);
      setNombre(r.cliente.nombre);
      setClientErrors({});
      setClientError(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSearching(false);
    }
  }

  async function onSaveClient(e: React.FormEvent) {
    e.preventDefault();
    if (!client) return;
    setClientError(null);
    setSuccess(null);
    const next = validateClient({ documento, nombre });
    setClientErrors(next);
    if (Object.keys(next).length > 0) return;
    setSavingClient(true);
    try {
      const r = await api.updateClient(client.id_cliente, {
        documento: documento.trim(),
        nombre: nombre.trim(),
      });
      // D-26: PUT does not return the vehicles; fetch the client again.
      const fresh = await api.client(client.id_cliente);
      setClient(fresh.cliente);
      setDocumento(fresh.cliente.documento);
      setNombre(fresh.cliente.nombre);
      setSuccess(r.mensaje ?? "Cliente actualizado correctamente.");
    } catch (err) {
      setClientError(errorMessage(err));
    } finally {
      setSavingClient(false);
    }
  }

  return (
    <>
      <PageHeader
        kicker="Administración"
        title="Clientes y vehículos"
        subtitle="Busca un vehículo por su placa para modificar los datos del cliente y de sus vehículos."
      />
      {success && <Alert kind="success" title={success} />}
      {error && <Alert kind="error" title={error} />}

      <StepCard step={1} kicker="Búsqueda" title="Buscar por placa">
        <form onSubmit={onSearch} className="flex gap-3">
          <div className="min-w-0 flex-1">
            <TextField
              label="Placa"
              value={plate}
              onChange={(e) => setPlate(e.target.value.toUpperCase())}
              placeholder="Ej. ABC123"
              autoComplete="off"
            />
          </div>
          <div className="flex items-end">
            <PrimaryButton type="submit" disabled={!plate.trim() || searching}>
              <Search size={16} />
              {searching ? "Buscando…" : "Buscar"}
            </PrimaryButton>
          </div>
        </form>
      </StepCard>

      {client && (
        <>
          <StepCard step={2} kicker="Cliente" title="Datos del cliente">
            <form onSubmit={onSaveClient} noValidate aria-label="Datos del cliente">
              {clientError && <Alert kind="error" title={clientError} />}
              <div className="grid gap-5 md:grid-cols-2">
                <TextField
                  label="Documento"
                  value={documento}
                  onChange={(e) => setDocumento(e.target.value)}
                  maxLength={20}
                  autoComplete="off"
                  error={clientErrors.documento}
                />
                <TextField
                  label="Nombre completo"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  maxLength={100}
                  autoComplete="off"
                  error={clientErrors.nombre}
                />
              </div>
              <div className="mt-5 flex justify-end">
                <PrimaryButton type="submit" disabled={savingClient}>
                  <Save size={16} />
                  {savingClient ? "Guardando…" : "Guardar cliente"}
                </PrimaryButton>
              </div>
            </form>
          </StepCard>
          <StepCard
            step={3}
            kicker="Vehículos"
            title={client.vehiculos.length === 1 ? "Vehículo del cliente" : "Vehículos del cliente"}
          >
            <div className="space-y-4">
              {client.vehiculos.map((v) => (
                <VehicleEditor
                  key={v.id_vehiculo}
                  vehicle={v}
                  highlighted={v.placa === searched}
                  onSaved={setSuccess}
                />
              ))}
            </div>
          </StepCard>
        </>
      )}
    </>
  );
}

export default function ClientsPage() {
  return (
    <RoleGate role="ADMINISTRADOR">
      <ClientsScreen />
    </RoleGate>
  );
}
