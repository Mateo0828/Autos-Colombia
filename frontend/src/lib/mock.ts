/**
 * [mock] In-memory fake of the Iteration 2 + 3 API. Since F-06 the payment shapes follow the REAL
 * backend (feature/i3-backend f4e988e, GUIA_INTEGRACION_FRONTEND_EA3, D-39), not contract 04.
 * Enabled only with NEXT_PUBLIC_USE_MOCK=true. Nothing here is verified
 * against the real backend. State is kept in sessionStorage so a page reload
 * (e.g. Playwright `goto`) does not reset it; closing the tab does.
 *
 * Dates and amounts: this file computes them ONLY to simulate the server
 * (D-32). Components never do; they show what the API answers.
 *
 * Test flags for POST /api/pagos (one-shot, read from sessionStorage "ac.mock.flags"
 * as JSON): {"force409":true} answers 409; {"force422":true} answers 422;
 * {"concurrent":true} registers a payment "by another operator" just before
 * this one, so the 409 comes from a real corte_esperado mismatch.
 * "ac.mock.fakeHoy"="AAAA-MM-DD" (sessionStorage) makes the server's "today" differ from the browser's day.
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
interface MPayment {
  id_pago: number;
  fecha_pago: string;
  valor: number;
  periodo_inicio: string;
  periodo_fin: string;
  registrado_por: MRegistrar;
  fecha_registro: string;
}
interface MRegistrar {
  id_operador: number;
  usuario: string;
  nombre: string;
}
interface MVehicle {
  id_vehiculo: number;
  placa: string;
  marca: string;
  color: string;
  tipo_vehiculo: "MOTO" | "AUTOMOVIL" | "CAMIONETA";
  id_cliente: number;
  /** D-31/D-32: anchor of the cut-off dates; estado_mensualidad is derived from it. */
  primer_pago: string | null;
  pagos: MPayment[];
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
  seq: { user: number; client: number; vehicle: number; stay: number; payment: number };
}

type Reply = { status: number; data: unknown };

const KEY = "ac.mock.i3";
const FLAGS_KEY = "ac.mock.flags";

// ---- [mock] date helpers, only to simulate the server ----
const pad2 = (n: number) => String(n).padStart(2, "0");
const isoOf = (y: number, m: number, d: number) => `${y}-${pad2(m)}-${pad2(d)}`;
const parts = (iso: string) => iso.split("-").map(Number) as [number, number, number];

function browserToday(): string {
  const d = new Date();
  return isoOf(d.getFullYear(), d.getMonth() + 1, d.getDate());
}
/** The mock server's "today" (can be faked from a test to differ from the browser's day). */
function todayStr(): string {
  try {
    return window.sessionStorage.getItem("ac.mock.fakeHoy") ?? browserToday();
  } catch {
    return browserToday();
  }
}
/** k months after iso, clamped to the last day of the target month (D-32). */
function addMonths(iso: string, k: number): string {
  const [y, m, d] = parts(iso);
  const total = y * 12 + (m - 1) + k;
  const ny = Math.floor(total / 12);
  const nm = (total % 12) + 1;
  return isoOf(ny, nm, Math.min(d, new Date(ny, nm, 0).getDate()));
}
function addDays(iso: string, n: number): string {
  const [y, m, d] = parts(iso);
  const t = new Date(y, m - 1, d + n);
  return isoOf(t.getFullYear(), t.getMonth() + 1, t.getDate());
}

const FEE: Record<MVehicle["tipo_vehiculo"], number> = { MOTO: 100000, AUTOMOVIL: 250000, CAMIONETA: 250000 };

/** Payments made on time, one per month, anchored on the first one. */
function payments(first: string, n: number, by: MRegistrar, idStart: number): MPayment[] {
  const out: MPayment[] = [];
  for (let k = 1; k <= n; k++) {
    const start = k === 1 ? first : addMonths(first, k - 1);
    out.push({
      id_pago: idStart + k - 1,
      fecha_pago: start,
      valor: 0, // filled by the caller (depends on vehicle type)
      periodo_inicio: start,
      periodo_fin: addMonths(first, k),
      registrado_por: by,
      fecha_registro: `${start}T09:00:00`,
    });
  }
  return out;
}

const MONTHLY_EXPIRED =
  "La mensualidad del vehículo se encuentra vencida. Debe registrar una renovación que restablezca su vigencia.";
const LATE_WARNING = "El período pagado no cubre la fecha actual. La mensualidad permanece inactiva.";

/** Derived monthly state (D-31): ACTIVA only while today < fecha_corte. */
function monthly(v: MVehicle) {
  const n = v.pagos.length;
  const corte = v.primer_pago && n > 0 ? addMonths(v.primer_pago, n) : null;
  return {
    n,
    inicio: v.primer_pago && n > 0 ? v.primer_pago : null,
    dia: v.primer_pago && n > 0 ? parts(v.primer_pago)[2] : null,
    corte,
    vigente: corte !== null && todayStr() < corte,
  };
}

/** Mirrors `proximo_pago` of GET /api/mensualidades/{placa}?fecha_pago= (real backend). */
function projection(v: MVehicle, fecha: string) {
  const mi = monthly(v);
  const first = mi.n === 0;
  const inicio = first ? fecha : (mi.corte as string);
  const fin = first ? addMonths(fecha, 1) : addMonths(v.primer_pago as string, mi.n + 1);
  const activa = todayStr() < fin;
  return {
    tipo: first ? "PRIMER_PAGO" : "RENOVACION",
    fecha_pago: fecha,
    valor: FEE[v.tipo_vehiculo],
    periodo_inicio: inicio,
    periodo_fin: fin,
    corte_esperado: mi.corte,
    estado_resultante: activa ? "ACTIVA" : "INACTIVA",
    advertencia: activa ? null : LATE_WARNING,
  };
}

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
  const today = todayStr();
  let payId = 1;
  const op1: MRegistrar = { id_operador: 1, usuario: "operador1", nombre: "Operador Mañana" };
  // `first` = date of the first payment; `n` = how many monthly payments were made.
  const v = (
    id: number,
    placa: string,
    marca: string,
    color: string,
    tipo: MVehicle["tipo_vehiculo"],
    id_cliente: number,
    first: string | null = null,
    n = 0,
  ): MVehicle => {
    const pagos = first ? payments(first, n, op1, payId).map((p) => ({ ...p, valor: FEE[tipo] })) : [];
    payId += pagos.length;
    return { id_vehiculo: id, placa, marca, color, tipo_vehiculo: tipo, id_cliente, primer_pago: first, pagos };
  };
  // Calendar demos (real seed: first payment on day 30 / 31 / 29-Feb), paid up to the next cut-off after today.
  const calendar = (first: string): number => {
    let n = 1;
    while (addMonths(first, n) <= today) n++;
    return n;
  };
  // First payment exactly one month before today => cut-off date == today (COR001).
  const corFirst =
    [28, 29, 30, 31].map((d) => addDays(today, -d)).find((c) => addMonths(c, 1) === today) ?? addMonths(today, -1);
  return {
    users: [
      u(1, "Operador Mañana", "operador1", "OPERADOR", "Operador123"),
      u(2, "Operador Tarde", "operador2", "OPERADOR", "Operador123"),
      u(3, "Operador Noche", "operador3", "OPERADOR", "Operador123"),
      u(4, "Administrador Autos Colombia", "admin", "ADMINISTRADOR", "Admin12345"),
    ],
    clients: [
      { id_cliente: 1, documento: "1012345678", nombre: "Carlos Rodriguez" },
      { id_cliente: 2, documento: "1023456789", nombre: "Laura Martinez" },
      { id_cliente: 3, documento: "1034567890", nombre: "Andres Gomez" },
      { id_cliente: 4, documento: "1045678901", nombre: "Diana Lopez" },
      { id_cliente: 5, documento: "EA3CAL030", nombre: "Demostracion calendario dia 30" },
      { id_cliente: 6, documento: "EA3CAL031", nombre: "Demostracion calendario dia 31" },
      { id_cliente: 7, documento: "EA3CAL029", nombre: "Demostracion calendario bisiesto" },
    ],
    // Same plates and scenarios as the real I3 seed, relative to today so they stay valid on any day.
    vehicles: [
      v(1, "ABC123", "Renault", "Blanco", "AUTOMOVIL", 1, addDays(today, -10), 1), // vigente
      v(2, "DEF456", "Mazda", "Rojo", "AUTOMOVIL", 2, addDays(today, -25), 1), // vigente
      v(3, "GHI789", "Toyota", "Gris", "CAMIONETA", 3, addDays(today, -15), 1), // vigente
      v(4, "MOT01A", "Yamaha", "Negro", "MOTO", 4, addDays(today, -12), 1), // moto vigente, 100000
      v(5, "JKL321", "Chevrolet", "Azul", "AUTOMOVIL", 1, addDays(addMonths(today, -1), -4), 1), // vencida hace 4 días
      v(6, "XYZ987", "Mazda", "Gris", "AUTOMOVIL", 2), // sin pagos
      v(7, "MOT02A", "Honda", "Negro", "MOTO", 4), // moto sin pagos
      v(8, "COR001", "Nissan", "Blanco", "AUTOMOVIL", 3, corFirst, 1), // corte == hoy (INACTIVA)
      v(9, "CAL030", "Renault", "Blanco", "AUTOMOVIL", 5, "2025-01-30", calendar("2025-01-30")),
      v(10, "CAL031", "Toyota", "Gris", "CAMIONETA", 6, "2025-01-31", calendar("2025-01-31")),
      v(11, "CAL029", "Honda", "Negro", "MOTO", 7, "2024-02-29", calendar("2024-02-29")),
    ],
    cells,
    stays: [],
    sessions: {},
    seq: { user: 5, client: 8, vehicle: 12, stay: 1, payment: payId },
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

const stateOf = (v: MVehicle): "ACTIVA" | "INACTIVA" => (monthly(v).vigente ? "ACTIVA" : "INACTIVA");

interface Flags {
  force409?: boolean;
  force422?: boolean;
  concurrent?: boolean;
}
/** One-shot test flags (see header). */
function takeFlags(): Flags {
  try {
    const raw = window.sessionStorage.getItem(FLAGS_KEY);
    if (!raw) return {};
    window.sessionStorage.removeItem(FLAGS_KEY);
    return JSON.parse(raw) as Flags;
  } catch {
    return {};
  }
}

/** One payment = one month, anchored on the first payment (D-32). The amount comes from the type. */
function applyPayment(s: MState, v: MVehicle, fecha: string, by: MRegistrar): MPayment {
  const n = v.pagos.length;
  if (n === 0) v.primer_pago = fecha;
  const first = v.primer_pago as string;
  const pago: MPayment = {
    id_pago: s.seq.payment++,
    fecha_pago: fecha,
    valor: FEE[v.tipo_vehiculo],
    periodo_inicio: n === 0 ? fecha : addMonths(first, n),
    periodo_fin: addMonths(first, n + 1),
    registrado_por: by,
    fecha_registro: nowIso(),
  };
  v.pagos.push(pago);
  return pago;
}

const registrar = (u: MUser): MRegistrar => ({ id_operador: u.id_operador, usuario: u.usuario, nombre: u.nombre });

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
      id_cliente: client.id_cliente,
      primer_pago: null, // D-31: INACTIVA, no dates, until the first payment
      pagos: [],
    };
    s.vehicles.push(veh);
    save();
    return ok(
      {
        cliente: client,
        vehiculo: { ...vehicleOut(veh), estado_mensualidad: "INACTIVA", fecha_inicio_mensualidad: null, fecha_corte: null },
      },
      201,
    );
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
        .map((x) => ({ ...vehicleOut(x), estado_mensualidad: stateOf(x) })),
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
    // D-31 / contract 04: the state is derived. The mock answers 422 so a UI that sends it fails its test.
    if (body.estado_mensualidad !== undefined)
      return err(422, "El estado de la mensualidad no puede modificarse; se deriva de los pagos.");
    if (!["MOTO", "AUTOMOVIL", "CAMIONETA"].includes(body.tipo_vehiculo)) return err(422, "Tipo de vehículo no válido.");
    if (body.tipo_vehiculo !== veh.tipo_vehiculo && s.stays.some((x) => x.id_vehiculo === veh.id_vehiculo))
      return err(409, "No se puede cambiar el tipo de un vehículo con estancia activa.");
    veh.marca = String(body.marca).trim();
    veh.color = String(body.color).trim();
    veh.tipo_vehiculo = body.tipo_vehiculo;
    save();
    return ok({
      mensaje: "Vehículo actualizado correctamente.",
      vehiculo: { ...vehicleOut(veh), id_cliente: veh.id_cliente, estado_mensualidad: stateOf(veh) },
    });
  }

  // ---- Iteration 3: payments (shapes of the real backend, GUIA_INTEGRACION_FRONTEND_EA3) ----
  const monm = m(/^\/api\/mensualidades\/([^/]+)$/);
  if (method === "GET" && monm) {
    const veh = s.vehicles.find((x) => x.placa === decodeURIComponent(monm[1]).toUpperCase());
    if (!veh) return err(404, "El vehículo no se encuentra registrado.");
    // Optional ?fecha_pago=AAAA-MM-DD; without it the server projects for its own "today".
    const fp = url.searchParams.get("fecha_pago");
    if (fp !== null && !/^\d{4}-\d{2}-\d{2}$/.test(fp)) return err(422, "La fecha de pago debe tener el formato YYYY-MM-DD.");
    if (fp !== null && fp > todayStr()) return err(422, "La fecha de pago no puede ser futura.");
    const mi = monthly(veh);
    const client = s.clients.find((x) => x.id_cliente === veh.id_cliente)!;
    return ok({
      vehiculo: vehicleOut(veh),
      cliente: client,
      tarifa: FEE[veh.tipo_vehiculo],
      estado_mensualidad: mi.vigente ? "ACTIVA" : "INACTIVA",
      fecha_inicio: mi.inicio,
      dia_corte: mi.dia,
      fecha_corte: mi.corte,
      num_pagos: mi.n,
      proximo_pago: projection(veh, fp ?? todayStr()),
    });
  }

  const hm = m(/^\/api\/vehiculos\/([^/]+)\/pagos$/);
  if (method === "GET" && hm) {
    const veh = s.vehicles.find((x) => x.placa === decodeURIComponent(hm[1]).toUpperCase());
    if (!veh) return err(404, "El vehículo no se encuentra registrado.");
    // Newest first. The history does not carry `tipo`.
    const list = [...veh.pagos].reverse().map((x) => ({
      id_pago: x.id_pago,
      valor: x.valor,
      fecha_pago: x.fecha_pago,
      fecha_registro: x.fecha_registro,
      periodo_inicio: x.periodo_inicio,
      periodo_fin: x.periodo_fin,
      registrado_por: x.registrado_por,
    }));
    return ok({ placa: veh.placa, cantidad: list.length, pagos: list });
  }

  if (method === "POST" && p === "/api/pagos") {
    // Exactly {placa, fecha_pago, corte_esperado}: anything else is 422 (the server owns the amount).
    const extra = Object.keys(body).filter((k) => !["placa", "fecha_pago", "corte_esperado"].includes(k));
    if (extra.length) return err(422, `Campos no autorizados: ${extra.join(", ")}.`);
    const missing = ["placa", "fecha_pago", "corte_esperado"].filter((k) => !(k in body));
    if (missing.length) return err(422, `Campos obligatorios faltantes: ${missing.join(", ")}.`);
    const flags = takeFlags();
    const fecha = String(body.fecha_pago ?? "");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) return err(422, "La fecha de pago debe tener el formato YYYY-MM-DD.");
    if (flags.force422) return err(422, "La fecha de pago no es válida.");
    if (fecha > todayStr()) return err(422, "La fecha de pago no puede ser futura.");
    const veh = s.vehicles.find((x) => x.placa === String(body.placa ?? "").trim().toUpperCase());
    if (!veh) return err(404, "El vehículo no se encuentra registrado.");
    // Another operator paid first: the next check then fails for real.
    if (flags.concurrent)
      applyPayment(s, veh, todayStr(), { id_operador: 2, usuario: "operador2", nombre: "Operador Tarde" });
    const before = monthly(veh);
    // null with payments, a value without payments, or a value that differs from the current cut-off -> 409.
    if (flags.force409 || body.corte_esperado !== before.corte)
      return err(409, "La mensualidad ya fue actualizada; consulte de nuevo.");
    const tipo = before.n === 0 ? "PRIMER_PAGO" : "RENOVACION";
    const pago = applyPayment(s, veh, fecha, registrar(me));
    const after = monthly(veh);
    save();
    return ok(
      {
        mensaje: "Pago registrado correctamente.",
        pago: { ...pago, placa: veh.placa, id_cliente: veh.id_cliente, tipo },
        mensualidad: {
          estado_mensualidad: after.vigente ? "ACTIVA" : "INACTIVA",
          fecha_inicio: after.inicio,
          dia_corte: after.dia,
          fecha_corte: after.corte,
          num_pagos: after.n,
        },
        advertencia: after.vigente ? null : LATE_WARNING,
      },
      201,
    );
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
        codigo_motivo: "VEHICULO_NO_REGISTRADO",
        motivo: "El vehículo no se encuentra registrado.",
        vehiculo: null,
        validaciones: { vehiculo_registrado: false, mensualidad_activa: false, sin_estancia_activa: false },
      });
    const inside = s.stays.some((x) => x.id_vehiculo === v.id_vehiculo);
    const mi = monthly(v);
    const active = mi.vigente;
    const client = s.clients.find((x) => x.id_cliente === v.id_cliente)!;
    const [codigo, motivo] =
      mi.n === 0
        ? ["SIN_PRIMER_PAGO", "El vehículo no tiene un primer pago de mensualidad registrado."]
        : !active
          ? ["MENSUALIDAD_VENCIDA", MONTHLY_EXPIRED]
          : inside
            ? ["ESTANCIA_ACTIVA", "El vehículo ya tiene una estancia activa."]
            : ["INGRESO_PERMITIDO", "El vehículo cumple las condiciones para ingresar."];
    return ok({
      puede_ingresar: codigo === "INGRESO_PERMITIDO",
      codigo_motivo: codigo,
      motivo,
      vehiculo: {
        ...vehicleOut(v),
        estado_mensualidad: stateOf(v),
        fecha_inicio_mensualidad: mi.inicio,
        fecha_corte: mi.corte,
        cliente: client,
      },
      validaciones: { vehiculo_registrado: true, mensualidad_activa: active, sin_estancia_activa: !inside },
    });
  }

  if (method === "POST" && p === "/api/entradas") {
    const v = s.vehicles.find((x) => x.placa === String(body.placa ?? "").toUpperCase());
    if (!v) return err(400, "El vehículo no se encuentra registrado.");
    if (monthly(v).n === 0) return err(400, "El vehículo no tiene un primer pago de mensualidad registrado.");
    if (!monthly(v).vigente) return err(400, MONTHLY_EXPIRED);
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
