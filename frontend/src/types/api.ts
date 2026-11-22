export type VehicleType = "MOTO" | "AUTOMOVIL" | "CAMIONETA";

export interface ApiError {
  estado: "error";
  mensaje: string;
}

export interface Operator {
  id_operador: number;
  nombre: string;
}

// ---- Authentication and users (contract 03) ----

export type Role = "ADMINISTRADOR" | "OPERADOR";
export type UserStatus = "ACTIVO" | "INACTIVO";

export interface SessionUser {
  id_operador: number;
  nombre: string;
  usuario: string;
  rol: Role;
}

export interface LoginResult {
  estado: "ok";
  token: string;
  expira: string;
  usuario: SessionUser;
}

export interface MeResult {
  estado: "ok";
  usuario: SessionUser;
}

export interface User extends SessionUser {
  estado: UserStatus;
  fecha_creacion: string;
}

export interface UserList {
  estado: "ok";
  usuarios: User[];
}

// Assumed shape (contract 03 only says "el usuario creado"): see report.
export interface UserResult {
  estado: "ok";
  mensaje?: string;
  usuario: User;
}

export interface MessageResult {
  estado: "ok";
  mensaje: string;
}

// ---- Clients and vehicles ----

export interface Client {
  id_cliente: number;
  documento: string;
  nombre: string;
}

export interface Vehicle {
  id_vehiculo: number;
  placa: string;
  marca: string;
  color: string;
  tipo_vehiculo: VehicleType;
}

// D-31: derived by the server from the cut-off date; read-only for the UI.
export type MonthlyState = "ACTIVA" | "INACTIVA";

export interface VehicleWithClient extends Vehicle {
  estado_mensualidad: string;
  // F-06: names used by the vehicle queries (the payment contract uses `fecha_inicio`).
  fecha_inicio_mensualidad?: string | null;
  fecha_corte?: string | null;
  cliente: Client;
}

export interface ClientDetail extends Client {
  vehiculos: (Vehicle & { estado_mensualidad: string })[];
}

// Assumed shape (contract 03: "Datos del cliente y sus vehículos").
export interface ClientResult {
  estado: "ok";
  mensaje?: string;
  cliente: ClientDetail;
}

// D-26: flat request body; response is {estado, cliente, vehiculo} without `mensaje`.
export interface RegistrationResult {
  estado: "ok";
  mensaje?: string;
  cliente?: Client;
  vehiculo?: Vehicle;
}

export interface VehicleResult {
  estado: "ok";
  mensaje?: string;
  vehiculo: Vehicle & { id_cliente?: number; estado_mensualidad?: string };
}

// D-26: PUT /api/clientes/{id} does not return the vehicle list.
export interface ClientUpdateResult {
  estado: "ok";
  mensaje?: string;
  cliente: Client;
}

/** F-06 (D-39): the UI decides by `puede_ingresar` and `codigo_motivo`; `motivo` is only displayed. */
export type EntryReason =
  | "VEHICULO_NO_REGISTRADO"
  | "SIN_PRIMER_PAGO"
  | "MENSUALIDAD_VENCIDA"
  | "ESTANCIA_ACTIVA"
  | "INGRESO_PERMITIDO";

export interface EntryValidation {
  estado: "ok";
  puede_ingresar: boolean;
  codigo_motivo: EntryReason;
  motivo: string;
  vehiculo: VehicleWithClient | null;
  validaciones: {
    vehiculo_registrado: boolean;
    // D-36: I2 name kept; in I3 it is derived from the cut-off date.
    mensualidad_activa: boolean;
    sin_estancia_activa: boolean;
  };
}

// ---- Cells ----

export type CellState = "DISPONIBLE" | "OCUPADA" | "FUERA_DE_SERVICIO";
export type CellType = "CARRO" | "MOTO";

export interface Cell {
  id_celda: number;
  codigo: string;
  tipo_celda: CellType;
  estado: CellState;
}

export interface AvailableCells {
  estado: "ok";
  cantidad: number;
  celdas: Cell[];
}

export interface CellList {
  estado: "ok";
  cantidad: number;
  celdas: Cell[];
}

export interface CellChange {
  estado: "ok";
  mensaje?: string;
  celda?: Cell;
}

// ---- Stays ----

export interface EntryResult {
  estado: "ok";
  mensaje: string;
  vehiculo: Vehicle;
  estancia: {
    id_estancia: number;
    fecha_hora_entrada: string;
    estado: string;
    celda: Cell;
    operador: Operator;
  };
}

export interface ActiveStay {
  id_estancia: number;
  vehiculo: Vehicle;
  celda: { id_celda: number; codigo: string };
  fecha_hora_entrada: string;
  operador_entrada: Operator;
}

export interface ActiveStays {
  estado: "ok";
  cantidad: number;
  vehiculos: ActiveStay[];
}

export interface ExitResult {
  estado: "ok";
  mensaje: string;
  placa: string;
  estancia: {
    id_estancia: number;
    fecha_hora_entrada: string;
    fecha_hora_salida: string;
    estado: string;
    celda: Cell;
    operador_salida: Operator;
  };
}

// ---- Payments (real backend I3, GUIA_INTEGRACION_FRONTEND_EA3, D-39). Dates are AAAA-MM-DD as sent by the server. ----

export type PaymentKind = "PRIMER_PAGO" | "RENOVACION";

/** F-06: `registrado_por` is an object everywhere; the UI shows `nombre`. */
export interface RegisteredBy {
  id_operador: number;
  usuario: string;
  nombre: string;
}

/** Server projection of the next payment for a given `fecha_pago` (nothing is computed by the UI). */
export interface NextPayment {
  tipo: PaymentKind;
  /** Date the projection was made for; for the first query it is the server's "today". */
  fecha_pago: string;
  valor: number | string;
  periodo_inicio: string;
  /** New cut-off date after this payment. */
  periodo_fin: string;
  /** Value to send back in POST /api/pagos; `null` only for the first payment. */
  corte_esperado: string | null;
  estado_resultante: MonthlyState;
  advertencia: string | null;
}

export interface MonthlyInfo {
  estado: "ok";
  vehiculo: Vehicle;
  cliente: Client;
  tarifa: number;
  estado_mensualidad: MonthlyState;
  fecha_inicio: string | null;
  dia_corte: number | null;
  fecha_corte: string | null;
  num_pagos: number;
  proximo_pago: NextPayment;
}

export interface PaymentBody {
  placa: string;
  fecha_pago: string;
  corte_esperado: string | null;
}

export interface PaymentResult {
  estado: "ok";
  mensaje: string;
  pago: {
    id_pago: number;
    placa: string;
    id_cliente: number;
    tipo: PaymentKind;
    // NUMERIC: may arrive as number or string; always rendered through formatMoney.
    valor: number | string;
    fecha_pago: string;
    fecha_registro: string;
    periodo_inicio: string;
    periodo_fin: string;
    registrado_por: RegisteredBy;
  };
  mensualidad: {
    estado_mensualidad: MonthlyState;
    fecha_inicio: string | null;
    dia_corte: number | null;
    fecha_corte: string | null;
    num_pagos: number;
  };
  advertencia: string | null;
}

/** The history does not carry `tipo`. */
export interface PaymentHistoryItem {
  id_pago: number;
  fecha_pago: string;
  valor: number | string;
  periodo_inicio: string;
  periodo_fin: string;
  registrado_por: RegisteredBy;
  fecha_registro: string;
}

export interface PaymentHistory {
  estado: "ok";
  placa: string;
  cantidad: number;
  pagos: PaymentHistoryItem[];
}

export interface CellGroup {
  total: number;
  disponibles: number;
  ocupadas: number;
}

export interface ParkingStatus {
  estado: "ok";
  vehiculos_dentro: number;
  celdas: CellGroup & {
    fuera_de_servicio?: number;
    carro: CellGroup;
    moto: CellGroup;
  };
}
