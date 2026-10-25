export type VehicleType = "MOTO" | "AUTOMOVIL" | "CAMIONETA";

export interface ApiError {
  estado: "error";
  mensaje: string;
}

export interface Operator {
  id_operador: number;
  nombre: string;
}

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

export interface Cell {
  id_celda: number;
  codigo: string;
  tipo_celda: "CARRO" | "MOTO";
  estado: "DISPONIBLE" | "OCUPADA";
}

export interface AvailableCells {
  estado: "ok";
  cantidad: number;
  celdas: Cell[];
}

export interface OperatorList {
  estado: "ok";
  cantidad: number;
  operadores: Operator[];
}

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
  celdas: CellGroup & { carro: CellGroup; moto: CellGroup };
}
