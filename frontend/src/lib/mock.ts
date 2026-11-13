/**
 * [mock] In-memory fake of the Iteration 2 API (contract 03 + 02).
 * Enabled only with NEXT_PUBLIC_USE_MOCK=true. Nothing here is verified
 * against the real backend. State is kept in sessionStorage so a page reload
 * (e.g. Playwright `goto`) does not reset it; closing the tab does.
 */

type Role = "ADMINISTRADOR" | "OPERADOR";
type CellState = "DISPONIBLE" | "OCUPADA" | "FUERA_DE_SERVICIO";

interface MUser {
  id_operador: number;
  nombre: string;
  usuario: string;
  rol: Role;
  estado: "ACTIVO" | "INACTIVO";
  fecha_creacion: string;
  password: string;
}
interface MClient {
  id_cliente: number;
  documento: string;
  nombre: string;
}
interface MVehicle {
  id_vehiculo: number;
  placa: string;
  marca: string;
  color: string;
  tipo_vehiculo: "MOTO" | "AUTOMOVIL" | "CAMIONETA";
  estado_mensualidad: "ACTIVA" | "INACTIVA";
  id_cliente: number;
}
interface MCell {
  id_celda: number;
  codigo: string;
  tipo_celda: "CARRO" | "MOTO";
  estado: CellState;
}
interface MStay {
  id_estancia: number;
  id_vehiculo: number;
  id_celda: number;
  entrada: string;
  id_operador: number;
}
interface MState {
  users: MUser[];
  clients: MClient[];
  vehicles: MVehicle[];
  cells: MCell[];
  stays: MStay[];
  sessions: Record<string, { id: number; revoked: boolean; expira: string }>;
  seq: { user: number; client: number; vehicle: number; stay: number };
}

type Reply = { status: number; data: unknown };

const KEY = "ac.mock";

function nowIso(offsetMs = 0): string {
  const d = new Date(Date.now() + offsetMs);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

function seed(): MState {
  const created = "2026-11-01T08:00:00";
  const u = (
    id: number,
    nombre: string,
    usuario: string,
    rol: Role,
    password: string,
  ): MUser => ({ id_operador: id, nombre, usuario, rol, estado: "ACTIVO", fecha_creacion: created, password });
  const cells: MCell[] = [];
  for (let i = 1; i <= 70; i++)
    cells.push({ id_celda: i, codigo: `C${String(i).padStart(2, "0")}`, tipo_celda: "CARRO", estado: "DISPONIBLE" });
  for (let i = 1; i <= 10; i++)
    cells.push({ id_celda: 70 + i, codigo: `M${String(i).padStart(2, "0")}`, tipo_celda: "MOTO", estado: "DISPONIBLE" });
  const v = (
    id: number,
    placa: string,
    marca: string,
    color: string,
    tipo: MVehicle["tipo_vehiculo"],
    estado: MVehicle["estado_mensualidad"],
    id_cliente: number,
  ): MVehicle => ({ id_vehiculo: id, placa, marca, color, tipo_vehiculo: tipo, estado_mensualidad: estado, id_cliente });
  return {
    users: [
      u(1, "Operador Mañana", "operador1", "OPERADOR", "Operador123"),
      u(2, "Operador Tarde", "operador2", "OPERADOR", "Operador123"),
      u(3, "Operador Noche", "operador3", "OPERADOR", "Operador123"),
      u(4, "Administrador Autos Colombia", "admin", "ADMINISTRADOR", "Admin12345"),
    ],
    clients: [
      { id_cliente: 1, documento: "1012345678", nombre: "Carlos Rodriguez" },
      { id_cliente: 2, documento: "1023456789", nombre: "Laura Gómez" },
      { id_cliente: 3, documento: "1034567890", nombre: "Andrés Pérez" },
      { id_cliente: 4, documento: "1045678901", nombre: "Marta Ruiz" },
    ],
    vehicles: [
      v(1, "ABC123", "Renault", "Blanco", "AUTOMOVIL", "ACTIVA", 1),
      v(2, "DEF456", "Mazda", "Rojo", "AUTOMOVIL", "ACTIVA", 2),
      v(3, "GHI789", "Toyota", "Gris", "CAMIONETA", "ACTIVA", 2),
      v(4, "MOT01A", "Yamaha", "Negro", "MOTO", "ACTIVA", 3),
      v(5, "JKL321", "Chevrolet", "Azul", "AUTOMOVIL", "INACTIVA", 4),
    ],
    cells,
    stays: [],
    sessions: {},
    seq: { user: 5, client: 5, vehicle: 6, stay: 1 },
  };
}

let state: MState | null = null;

function load(): MState {
  if (state) return state;
  try {
    const raw = typeof window !== "undefined" ? window.sessionStorage.getItem(KEY) : null;
    if (raw) {
      state = JSON.parse(raw) as MState;
      return state;
    }
  } catch {
    // fall through to a fresh seed
  }
  state = seed();
  return state;
}

function save() {
  if (state && typeof window !== "undefined") window.sessionStorage.setItem(KEY, JSON.stringify(state));
}

const err = (status: number, mensaje: string): Reply => ({ status, data: { estado: "error", mensaje } });
const ok = (data: object, status = 200): Reply => ({ status, data: { estado: "ok", ...data } });

const publicUser = (u: MUser) => ({
  id_operador: u.id_operador,
  nombre: u.nombre,
  usuario: u.usuario,
  rol: u.rol,
  estado: u.estado,
  fecha_creacion: u.fecha_creacion,
});
const sessionUser = (u: MUser) => ({
  id_operador: u.id_operador,
  nombre: u.nombre,
  usuario: u.usuario,
  rol: u.rol,
});
const vehicleOut = (v: MVehicle) => ({
  id_vehiculo: v.id_vehiculo,
  placa: v.placa,
  marca: v.marca,
  color: v.color,
  tipo_vehiculo: v.tipo_vehiculo,
});
const cellOut = (c: MCell) => ({ id_celda: c.id_celda, codigo: c.codigo, tipo_celda: c.tipo_celda, estado: c.estado });

const PLATE_RE = /^[A-Za-z0-9]{1,10}$/;
const blank = (s: unknown) => typeof s !== "string" || s.trim() === "";

export async function mockRequest(
  path: string,
  init: { method?: string; body?: BodyInit | null; headers?: Record<string, string> },
): Promise<Reply> {
  await new Promise((r) => setTimeout(r, 60));
  const s = load();
  const method = (init.method ?? "GET").toUpperCase();
  const url = new URL(path, "http://mock");
  const p = url.pathname;
  const body: Record<string, any> = init.body ? JSON.parse(String(init.body)) : {}; // eslint-disable-line @typescript-eslint/no-explicit-any
  const m = (re: RegExp) => p.match(re);

  // ---- login (public) ----
  if (method === "POST" && p === "/api/auth/login") {
    if (blank(body.usuario) || blank(body.password)) return err(422, "Usuario y contraseña son obligatorios.");
    const u = s.users.find((x) => x.usuario === String(body.usuario).trim().toLowerCase());
    if (!u || u.estado !== "ACTIVO" || u.password !== body.password)
      return err(401, "Usuario o contraseña incorrectos.");
    const token = `mock-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
    const expira = nowIso(8 * 3600 * 1000);
    s.sessions[token] = { id: u.id_operador, revoked: false, expira };
    save();
    return ok({ token, expira, usuario: sessionUser(u) });
  }

  // ---- everything else needs a session ----
  const token = (init.headers?.Authorization ?? "").replace(/^Bearer /, "");
  const sess = token ? s.sessions[token] : undefined;
  const me = sess && !sess.revoked ? s.users.find((x) => x.id_operador === sess.id) : undefined;
  if (!me || me.estado !== "ACTIVO") return err(401, "Sesión no válida o vencida. Inicie sesión de nuevo.");
  const admin = me.rol === "ADMINISTRADOR";
  const forbid = () => err(403, "No tiene permisos para realizar esta acción.");

  if (method === "POST" && p === "/api/auth/logout") {
    sess!.revoked = true;
    save();
    return ok({ mensaje: "Sesión cerrada correctamente." });
  }
  if (method === "GET" && p === "/api/auth/me") return ok({ usuario: sessionUser(me) });

  // ---- users ----
  if (p === "/api/usuarios" || p.startsWith("/api/usuarios/")) {
    if (!admin) return forbid();
    if (method === "GET" && p === "/api/usuarios")
      return ok({ usuarios: s.users.map(publicUser) });
    if (method === "POST" && p === "/api/usuarios") {
      if (blank(body.nombre) || blank(body.usuario) || blank(body.password) || blank(body.rol))
        return err(422, "Todos los campos son obligatorios.");
      if (body.rol !== "ADMINISTRADOR" && body.rol !== "OPERADOR") return err(422, "Rol no válido.");
      if (String(body.password).length < 8) return err(422, "La contraseña debe tener al menos 8 caracteres.");
      const usuario = String(body.usuario).trim().toLowerCase();
      if (s.users.some((x) => x.usuario === usuario)) return err(409, "El usuario ya existe.");
      const u: MUser = {
        id_operador: s.seq.user++,
        nombre: String(body.nombre).trim(),
        usuario,
        rol: body.rol,
        estado: "ACTIVO",
        fecha_creacion: nowIso(),
        password: body.password,
      };
      s.users.push(u);
      save();
      return ok({ mensaje: "Usuario creado correctamente.", usuario: publicUser(u) }, 201);
    }
    const um = m(/^\/api\/usuarios\/(\d+)(\/estado)?$/);
    if (um) {
      const u = s.users.find((x) => x.id_operador === Number(um[1]));
      if (!u) return err(404, "Usuario no encontrado.");
      const activeAdmins = s.users.filter((x) => x.rol === "ADMINISTRADOR" && x.estado === "ACTIVO");
      if (method === "PUT" && !um[2]) {
        if (blank(body.nombre)) return err(422, "El nombre es obligatorio.");
        if (body.rol !== undefined && body.rol !== "ADMINISTRADOR" && body.rol !== "OPERADOR")
          return err(422, "Rol no válido.");
        if (body.password !== undefined && body.password !== "" && String(body.password).length < 8)
          return err(422, "La contraseña debe tener al menos 8 caracteres.");
        if (
          body.rol === "OPERADOR" &&
          u.rol === "ADMINISTRADOR" &&
          u.estado === "ACTIVO" &&
          activeAdmins.length === 1
        )
          return err(409, "Debe existir al menos un administrador activo.");
        u.nombre = String(body.nombre).trim();
        if (body.rol) u.rol = body.rol;
        if (body.password) u.password = body.password;
        save();
        return ok({ mensaje: "Usuario actualizado correctamente.", usuario: publicUser(u) });
      }
      if (method === "PATCH" && um[2]) {
        if (body.estado !== "ACTIVO" && body.estado !== "INACTIVO") return err(422, "Estado no válido.");
        if (body.estado === "INACTIVO") {
          if (u.id_operador === me.id_operador) return err(409, "No puede inactivar su propio usuario.");
          if (u.rol === "ADMINISTRADOR" && u.estado === "ACTIVO" && activeAdmins.length === 1)
            return err(409, "Debe existir al menos un administrador activo.");
          for (const t of Object.values(s.sessions)) if (t.id === u.id_operador) t.revoked = true;
        }
        u.estado = body.estado;
        save();
        return ok({ mensaje: "Estado actualizado correctamente.", usuario: publicUser(u) });
      }
    }
    return err(404, "Recurso no encontrado.");
  }

  // ---- registration, clients, vehicles ----
  if (method === "POST" && p === "/api/registros") {
    // D-26: flat body
    const c = body;
    const v = body;
    if (blank(c.documento) || blank(c.nombre) || blank(v.placa) || blank(v.marca) || blank(v.color))
      return err(422, "Todos los campos son obligatorios.");
    if (!PLATE_RE.test(String(v.placa).trim())) return err(422, "La placa solo puede contener letras y números (máximo 10).");
    if (!["MOTO", "AUTOMOVIL", "CAMIONETA"].includes(v.tipo_vehiculo)) return err(422, "Tipo de vehículo no válido.");
    const placa = String(v.placa).trim().toUpperCase();
    if (s.vehicles.some((x) => x.placa === placa)) return err(409, "La placa ya se encuentra registrada.");
    let client = s.clients.find((x) => x.documento === String(c.documento).trim());
    if (!client) {
      client = { id_cliente: s.seq.client++, documento: String(c.documento).trim(), nombre: String(c.nombre).trim() };
      s.clients.push(client);
    }
    const veh: MVehicle = {
      id_vehiculo: s.seq.vehicle++,
      placa,
      marca: String(v.marca).trim(),
      color: String(v.color).trim(),
      tipo_vehiculo: v.tipo_vehiculo,
      estado_mensualidad: "ACTIVA",
      id_cliente: client.id_cliente,
    };
    s.vehicles.push(veh);
    save();
    return ok({ cliente: client, vehiculo: vehicleOut(veh) }, 201);
  }

  const cm = m(/^\/api\/clientes\/(\d+)$/);
  if (cm) {
    if (!admin) return forbid();
    const c = s.clients.find((x) => x.id_cliente === Number(cm[1]));
    if (!c) return err(404, "Cliente no encontrado.");
    const detail = () => ({
      ...c,
      vehiculos: s.vehicles
        .filter((x) => x.id_cliente === c.id_cliente)
        .map((x) => ({ ...vehicleOut(x), estado_mensualidad: x.estado_mensualidad })),
    });
    if (method === "GET") return ok({ cliente: detail() });
    if (method === "PUT") {
      if (blank(body.documento) || blank(body.nombre)) return err(422, "Documento y nombre son obligatorios.");
      const doc = String(body.documento).trim();
      if (s.clients.some((x) => x.documento === doc && x.id_cliente !== c.id_cliente))
        return err(409, "Ya existe otro cliente con ese documento.");
      c.documento = doc;
      c.nombre = String(body.nombre).trim();
      save();
      return ok({ mensaje: "Cliente actualizado correctamente.", cliente: { id_cliente: c.id_cliente, documento: c.documento, nombre: c.nombre } });
    }
  }

  const vm = m(/^\/api\/vehiculos\/([^/]+)$/);
  if (vm && method === "PUT") {
    if (!admin) return forbid();
    const veh = s.vehicles.find((x) => x.placa === decodeURIComponent(vm[1]).toUpperCase());
    if (!veh) return err(404, "Vehículo no encontrado.");
    if (body.placa !== undefined) return err(422, "La placa del vehículo no puede modificarse.");
    if (blank(body.marca) || blank(body.color)) return err(422, "Todos los campos son obligatorios.");
    if (body.estado_mensualidad !== undefined && !["ACTIVA", "INACTIVA"].includes(body.estado_mensualidad))
      return err(422, "Estado de mensualidad no válido.");
    if (!["MOTO", "AUTOMOVIL", "CAMIONETA"].includes(body.tipo_vehiculo)) return err(422, "Tipo de vehículo no válido.");
    if (body.tipo_vehiculo !== veh.tipo_vehiculo && s.stays.some((x) => x.id_vehiculo === veh.id_vehiculo))
      return err(409, "No se puede cambiar el tipo de un vehículo con estancia activa.");
    if (body.estado_mensualidad) veh.estado_mensualidad = body.estado_mensualidad;
    veh.marca = String(body.marca).trim();
    veh.color = String(body.color).trim();
    veh.tipo_vehiculo = body.tipo_vehiculo;
    save();
    return ok({ mensaje: "Vehículo actualizado correctamente.", vehiculo: vehicleOut(veh) });
  }

  // ---- cells ----
  if (method === "GET" && p === "/api/celdas") {
    if (!admin) return forbid();
    const estado = url.searchParams.get("estado");
    const tipo = url.searchParams.get("tipo");
    const q = (url.searchParams.get("q") ?? "").toLowerCase();
    const list = s.cells.filter(
      (c) => (!estado || c.estado === estado) && (!tipo || c.tipo_celda === tipo) && c.codigo.toLowerCase().includes(q),
    );
    return ok({ cantidad: list.length, celdas: list.map(cellOut) });
  }
  const dm = m(/^\/api\/celdas\/([^/]+)\/(deshabilitar|habilitar)$/);
  if (dm && method === "PATCH") {
    if (!admin) return forbid();
    const c = s.cells.find((x) => x.codigo === decodeURIComponent(dm[1]).toUpperCase());
    if (!c) return err(404, "La celda no existe.");
    if (dm[2] === "deshabilitar") {
      if (c.estado === "OCUPADA") return err(409, "No se puede deshabilitar una celda ocupada.");
      if (c.estado === "FUERA_DE_SERVICIO") return err(409, "La celda ya se encuentra fuera de servicio.");
      c.estado = "FUERA_DE_SERVICIO";
    } else {
      if (c.estado !== "FUERA_DE_SERVICIO") return err(409, "La celda no se encuentra fuera de servicio.");
      c.estado = "DISPONIBLE";
    }
    save();
    return ok({ mensaje: "Celda actualizada correctamente.", celda: cellOut(c) });
  }
  if (method === "GET" && p === "/api/celdas/disponibles") {
    const t = url.searchParams.get("tipo_vehiculo");
    if (!t || !["MOTO", "AUTOMOVIL", "CAMIONETA"].includes(t)) return err(400, "Tipo de vehículo no válido.");
    const kind = t === "MOTO" ? "MOTO" : "CARRO";
    const list = s.cells.filter((c) => c.tipo_celda === kind && c.estado === "DISPONIBLE");
    return ok({ cantidad: list.length, celdas: list.map(cellOut) });
  }

  // ---- Iteration 1 ----
  const valm = m(/^\/api\/vehiculos\/([^/]+)\/validar-ingreso$/);
  if (method === "GET" && valm) {
    const plate = decodeURIComponent(valm[1]).toUpperCase();
    if (!PLATE_RE.test(plate)) return err(400, "La placa solo puede contener letras y números (máximo 10).");
    const v = s.vehicles.find((x) => x.placa === plate);
    if (!v)
      return ok({
        puede_ingresar: false,
        motivo: "El vehículo no se encuentra registrado.",
        vehiculo: null,
        validaciones: { vehiculo_registrado: false, mensualidad_activa: false, sin_estancia_activa: false },
      });
    const inside = s.stays.some((x) => x.id_vehiculo === v.id_vehiculo);
    const active = v.estado_mensualidad === "ACTIVA";
    const client = s.clients.find((x) => x.id_cliente === v.id_cliente)!;
    return ok({
      puede_ingresar: active && !inside,
      motivo: !active
        ? "La mensualidad del vehículo se encuentra inactiva."
        : inside
          ? "El vehículo ya tiene una estancia activa."
          : "El vehículo cumple las condiciones para ingresar.",
      vehiculo: { ...vehicleOut(v), estado_mensualidad: v.estado_mensualidad, cliente: client },
      validaciones: { vehiculo_registrado: true, mensualidad_activa: active, sin_estancia_activa: !inside },
    });
  }

  if (method === "POST" && p === "/api/entradas") {
    const v = s.vehicles.find((x) => x.placa === String(body.placa ?? "").toUpperCase());
    if (!v) return err(400, "El vehículo no se encuentra registrado.");
    if (v.estado_mensualidad !== "ACTIVA") return err(400, "La mensualidad del vehículo se encuentra inactiva.");
    if (s.stays.some((x) => x.id_vehiculo === v.id_vehiculo)) return err(400, "El vehículo ya tiene una estancia activa.");
    const c = s.cells.find((x) => x.codigo === String(body.codigo_celda ?? "").toUpperCase());
    if (!c) return err(400, "La celda no existe.");
    if (c.estado === "OCUPADA") return err(400, "La celda seleccionada se encuentra ocupada.");
    if (c.estado === "FUERA_DE_SERVICIO") return err(400, "La celda seleccionada se encuentra fuera de servicio.");
    if ((v.tipo_vehiculo === "MOTO") !== (c.tipo_celda === "MOTO")) return err(400, "La celda no es compatible con el tipo de vehículo.");
    c.estado = "OCUPADA";
    const stay: MStay = { id_estancia: s.seq.stay++, id_vehiculo: v.id_vehiculo, id_celda: c.id_celda, entrada: nowIso(), id_operador: me.id_operador };
    s.stays.push(stay);
    save();
    return ok(
      {
        mensaje: "Entrada registrada correctamente.",
        vehiculo: vehicleOut(v),
        estancia: {
          id_estancia: stay.id_estancia,
          fecha_hora_entrada: stay.entrada,
          estado: "ACTIVA",
          celda: cellOut(c),
          operador: { id_operador: me.id_operador, nombre: me.nombre },
        },
      },
      201,
    );
  }

  if (method === "GET" && p === "/api/estancias/activas") {
    const list = s.stays.map((st) => {
      const v = s.vehicles.find((x) => x.id_vehiculo === st.id_vehiculo)!;
      const c = s.cells.find((x) => x.id_celda === st.id_celda)!;
      const o = s.users.find((x) => x.id_operador === st.id_operador)!;
      return {
        id_estancia: st.id_estancia,
        vehiculo: vehicleOut(v),
        celda: { id_celda: c.id_celda, codigo: c.codigo },
        fecha_hora_entrada: st.entrada,
        operador_entrada: { id_operador: o.id_operador, nombre: o.nombre },
      };
    });
    return ok({ cantidad: list.length, vehiculos: list });
  }

  if (method === "POST" && p === "/api/salidas") {
    const plate = String(body.placa ?? "").toUpperCase();
    const v = s.vehicles.find((x) => x.placa === plate);
    const idx = v ? s.stays.findIndex((x) => x.id_vehiculo === v.id_vehiculo) : -1;
    if (!v || idx < 0) return err(400, "El vehículo no tiene una estancia activa.");
    const st = s.stays[idx];
    const c = s.cells.find((x) => x.id_celda === st.id_celda)!;
    c.estado = "DISPONIBLE";
    s.stays.splice(idx, 1);
    save();
    return ok({
      mensaje: "Salida registrada correctamente.",
      placa: v.placa,
      estancia: {
        id_estancia: st.id_estancia,
        fecha_hora_entrada: st.entrada,
        fecha_hora_salida: nowIso(),
        estado: "FINALIZADA",
        celda: cellOut(c),
        operador_salida: { id_operador: me.id_operador, nombre: me.nombre },
      },
    });
  }

  if (method === "GET" && p === "/api/parqueadero/estado") {
    const g = (kind?: "CARRO" | "MOTO") => {
      const l = s.cells.filter((c) => !kind || c.tipo_celda === kind);
      return {
        total: l.length,
        disponibles: l.filter((c) => c.estado === "DISPONIBLE").length,
        ocupadas: l.filter((c) => c.estado === "OCUPADA").length,
      };
    };
    return ok({
      vehiculos_dentro: s.stays.length,
      celdas: {
        ...g(),
        fuera_de_servicio: s.cells.filter((c) => c.estado === "FUERA_DE_SERVICIO").length,
        carro: g("CARRO"),
        moto: g("MOTO"),
      },
    });
  }

  return err(404, "Recurso no encontrado.");
}
