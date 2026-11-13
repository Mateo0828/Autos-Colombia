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

export interface VehicleWithClient extends Vehicle {
  estado_mensualidad: string;
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

export interface EntryValidation {
  estado: "ok";
  puede_ingresar: boolean;
  motivo: string;
  vehiculo: VehicleWithClient | null;
  validaciones: {
    vehiculo_registrado: boolean;
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
