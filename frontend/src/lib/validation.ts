import { PLATE_ERROR, isValidPlate } from "@/lib/format";

// Client-side validation mirrors (never replaces) the server's. Messages in Spanish.
export type FieldErrors = Record<string, string>;

const DOCUMENT_RE = /^[A-Za-z0-9]{1,20}$/;
const DOCUMENT_ERROR = "El documento solo puede contener letras y números (máximo 20).";

export function validateClient(v: { documento: string; nombre: string }): FieldErrors {
  const e: FieldErrors = {};
  if (!v.documento.trim()) e.documento = "El documento es obligatorio.";
  else if (!DOCUMENT_RE.test(v.documento.trim())) e.documento = DOCUMENT_ERROR;
  if (!v.nombre.trim()) e.nombre = "El nombre es obligatorio.";
  else if (v.nombre.trim().length > 100) e.nombre = "El nombre admite máximo 100 caracteres.";
  return e;
}

export function validateVehicle(v: {
  placa: string;
  marca: string;
  color: string;
  tipo: string;
}): FieldErrors {
  const e: FieldErrors = {};
  if (!v.placa.trim()) e.placa = "La placa es obligatoria.";
  else if (!isValidPlate(v.placa.trim().toUpperCase())) e.placa = PLATE_ERROR;
  if (!v.marca.trim()) e.marca = "La marca es obligatoria.";
  else if (v.marca.trim().length > 50) e.marca = "La marca admite máximo 50 caracteres.";
  if (!v.color.trim()) e.color = "El color es obligatorio.";
  else if (v.color.trim().length > 30) e.color = "El color admite máximo 30 caracteres.";
  if (!v.tipo) e.tipo = "Selecciona el tipo de vehículo.";
  return e;
}

export function validateUser(
  v: { nombre: string; usuario?: string; password: string; rol: string },
  opts: { creating: boolean },
): FieldErrors {
  const e: FieldErrors = {};
  if (!v.nombre.trim()) e.nombre = "El nombre es obligatorio.";
  if (opts.creating) {
    if (!v.usuario?.trim()) e.usuario = "El usuario es obligatorio.";
    else if (/\s/.test(v.usuario.trim())) e.usuario = "El usuario no puede contener espacios.";
  }
  if (!v.rol) e.rol = "Selecciona un rol.";
  if (opts.creating) {
    if (!v.password) e.password = "La contraseña es obligatoria.";
    else if (!v.password.trim()) e.password = "La contraseña no puede ser solo espacios.";
    else if (v.password.length < 8) e.password = "La contraseña debe tener al menos 8 caracteres.";
  } else if (v.password && v.password.length < 8) {
    e.password = "La contraseña debe tener al menos 8 caracteres.";
  }
  return e;
}
