"use client";

import { useCallback, useEffect, useState } from "react";
import { Pencil, Plus, Power, Save, X } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { validateUser, type FieldErrors } from "@/lib/validation";
import { formatDateTime } from "@/lib/format";
import type { Role, User } from "@/types/api";
import { useAuth } from "@/components/AuthContext";
import RoleGate from "@/components/RoleGate";
import PageHeader from "@/components/PageHeader";
import { SecondaryButton, SelectField, TextField } from "@/components/Fields";
import PrimaryButton from "@/components/PrimaryButton";
import ConfirmDialog from "@/components/ConfirmDialog";
import Alert from "@/components/Alert";

const ROLE_LABEL: Record<Role, string> = {
  ADMINISTRADOR: "Administrador",
  OPERADOR: "Operador",
};

interface FormState {
  nombre: string;
  usuario: string;
  password: string;
  rol: Role | "";
}
const EMPTY: FormState = { nombre: "", usuario: "", password: "", rol: "" };

function UsersScreen() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // `editing`: null = form closed, "new" = creating, User = editing that user.
  const [editing, setEditing] = useState<User | "new" | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [saving, setSaving] = useState(false);

  const [toggle, setToggle] = useState<User | null>(null);
  const [toggling, setToggling] = useState(false);

  const load = useCallback(async () => {
    try {
      setUsers((await api.users()).usuarios);
      setLoadError(null);
    } catch (e) {
      setLoadError(errorMessage(e));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function openNew() {
    setEditing("new");
    setForm(EMPTY);
    setErrors({});
    setError(null);
    setSuccess(null);
  }

  function openEdit(u: User) {
    setEditing(u);
    setForm({ nombre: u.nombre, usuario: u.usuario, password: "", rol: u.rol });
    setErrors({});
    setError(null);
    setSuccess(null);
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    if (editing === null) return;
    const creating = editing === "new";
    const next = validateUser(form, { creating });
    setErrors(next);
    setError(null);
    if (Object.keys(next).length > 0 || form.rol === "") return;
    setSaving(true);
    try {
      if (creating) {
        const r = await api.createUser({
          nombre: form.nombre.trim(),
          usuario: form.usuario.trim(),
          password: form.password,
          rol: form.rol,
        });
        setSuccess(r.mensaje ?? `Usuario ${form.usuario.trim().toLowerCase()} creado correctamente.`);
      } else {
        const r = await api.updateUser(editing.id_operador, {
          nombre: form.nombre.trim(),
          rol: form.rol,
          ...(form.password ? { password: form.password } : {}),
        });
        setSuccess(r.mensaje ?? "Usuario actualizado correctamente.");
      }
      setEditing(null);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function onToggle() {
    if (!toggle) return;
    const target = toggle.estado === "ACTIVO" ? "INACTIVO" : "ACTIVO";
    setToggling(true);
    setError(null);
    setSuccess(null);
    try {
      const r = await api.setUserStatus(toggle.id_operador, target);
      setSuccess(
        r.mensaje ??
          (target === "INACTIVO"
            ? `Usuario ${toggle.usuario} inactivado.`
            : `Usuario ${toggle.usuario} activado.`),
      );
      setToggle(null);
      await load();
    } catch (err) {
      setError(errorMessage(err));
      setToggle(null);
    } finally {
      setToggling(false);
    }
  }

  return (
    <>
      <PageHeader
        kicker="Administración"
        title="Usuarios"
        subtitle="Crea, edita e inactiva operadores y administradores. Un usuario inactivo no puede iniciar sesión y su historial se conserva."
      />

      {success && <Alert kind="success" title={success} />}
      {error && <Alert kind="error" title={error} />}
      {loadError && <Alert kind="error" title={loadError} />}

      {editing !== null && (
        <form
          onSubmit={onSave}
          noValidate
          aria-label={editing === "new" ? "Nuevo usuario" : "Editar usuario"}
          className="mb-6 rounded-2xl border border-line bg-card p-6"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-lg">{editing === "new" ? "Nuevo usuario" : `Editar ${editing.usuario}`}</h2>
            <button
              type="button"
              aria-label="Cerrar formulario"
              onClick={() => setEditing(null)}
              className="text-muted hover:text-foreground"
            >
              <X size={18} />
            </button>
          </div>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <TextField
              label="Nombre"
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              autoComplete="off"
              error={errors.nombre}
            />
            <TextField
              label="Usuario"
              value={form.usuario}
              onChange={(e) => setForm({ ...form, usuario: e.target.value })}
              autoComplete="off"
              disabled={editing !== "new"}
              hint={editing !== "new" ? "El usuario no se puede modificar." : "Se guarda en minúsculas."}
              error={errors.usuario}
            />
            <SelectField
              label="Rol"
              value={form.rol}
              onChange={(e) => setForm({ ...form, rol: e.target.value as Role | "" })}
              error={errors.rol}
            >
              <option value="">Seleccione un rol</option>
              <option value="OPERADOR">Operador</option>
              <option value="ADMINISTRADOR">Administrador</option>
            </SelectField>
            <TextField
              label={editing === "new" ? "Contraseña" : "Nueva contraseña (opcional)"}
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              autoComplete="new-password"
              hint="Mínimo 8 caracteres."
              error={errors.password}
            />
          </div>
          <div className="mt-6 flex justify-end gap-3">
            <SecondaryButton onClick={() => setEditing(null)}>Cancelar</SecondaryButton>
            <PrimaryButton type="submit" disabled={saving}>
              <Save size={16} />
              {saving ? "Guardando…" : "Guardar"}
            </PrimaryButton>
          </div>
        </form>
      )}

      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-muted">
          <span className="text-2xl font-bold text-accent">{users?.length ?? "–"}</span> usuarios
        </p>
        <PrimaryButton onClick={openNew}>
          <Plus size={16} />
          Nuevo usuario
        </PrimaryButton>
      </div>

      {!users && !loadError && <p className="text-sm text-muted">Cargando…</p>}
      {users && (
        <div className="overflow-x-auto rounded-2xl border border-line bg-card">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead>
              <tr className="border-b border-line text-[10px] uppercase tracking-widest text-muted">
                {["Nombre", "Usuario", "Rol", "Estado", "Creado", ""].map((h, i) => (
                  <th key={i} className="px-5 py-4 font-bold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const active = u.estado === "ACTIVO";
                return (
                  <tr
                    key={u.id_operador}
                    data-testid={`user-row-${u.usuario}`}
                    className="border-b border-line last:border-0"
                  >
                    <td className="px-5 py-4 font-bold">{u.nombre}</td>
                    <td className="px-5 py-4">{u.usuario}</td>
                    <td className="px-5 py-4">{ROLE_LABEL[u.rol]}</td>
                    <td className="px-5 py-4">
                      <span
                        className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-wider ${
                          active
                            ? "border-success/50 bg-success/10 text-success"
                            : "border-danger/50 bg-danger/10 text-danger"
                        }`}
                      >
                        {u.estado}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-muted">{formatDateTime(u.fecha_creacion)}</td>
                    <td className="px-5 py-4">
                      <div className="flex justify-end gap-2">
                        <SecondaryButton onClick={() => openEdit(u)} aria-label={`Editar ${u.usuario}`}>
                          <Pencil size={14} />
                          Editar
                        </SecondaryButton>
                        <SecondaryButton
                          onClick={() => setToggle(u)}
                          disabled={u.id_operador === me?.id_operador && active}
                          title={
                            u.id_operador === me?.id_operador && active
                              ? "No puedes inactivar tu propio usuario."
                              : undefined
                          }
                          aria-label={`${active ? "Inactivar" : "Activar"} ${u.usuario}`}
                        >
                          <Power size={14} />
                          {active ? "Inactivar" : "Activar"}
                        </SecondaryButton>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {toggle && (
        <ConfirmDialog
          title={toggle.estado === "ACTIVO" ? "Inactivar usuario" : "Activar usuario"}
          message={
            toggle.estado === "ACTIVO"
              ? `${toggle.nombre} (${toggle.usuario}) no podrá iniciar sesión y se cerrarán sus sesiones abiertas. Su historial se conserva.`
              : `${toggle.nombre} (${toggle.usuario}) podrá volver a iniciar sesión.`
          }
          confirmLabel={toggle.estado === "ACTIVO" ? "Inactivar" : "Activar"}
          busy={toggling}
          onConfirm={onToggle}
          onCancel={() => setToggle(null)}
        />
      )}
    </>
  );
}

export default function UsersPage() {
  return (
    <RoleGate role="ADMINISTRADOR">
      <UsersScreen />
    </RoleGate>
  );
}
