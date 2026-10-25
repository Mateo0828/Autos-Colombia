import type {
  ActiveStays,
  AvailableCells,
  EntryResult,
  EntryValidation,
  ExitResult,
  OperatorList,
  ParkingStatus,
  VehicleType,
} from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:5000";

export const CONNECTION_ERROR = "No se pudo conectar con el servidor";

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public status: number | null,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      cache: "no-store",
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiRequestError(CONNECTION_ERROR, null);
  }
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    // non-JSON body handled below
  }
  if (!res.ok) {
    const msg =
      data && typeof data === "object" && "mensaje" in data
        ? String((data as { mensaje: unknown }).mensaje)
        : "Ocurrió un error inesperado en el servidor.";
    throw new ApiRequestError(msg, res.status);
  }
  return data as T;
}

export function errorMessage(e: unknown): string {
  return e instanceof Error ? e.message : CONNECTION_ERROR;
}

export const api = {
  validateEntry: (plate: string) =>
    request<EntryValidation>(
      `/api/vehiculos/${encodeURIComponent(plate)}/validar-ingreso`,
    ),
  availableCells: (type: VehicleType) =>
    request<AvailableCells>(`/api/celdas/disponibles?tipo_vehiculo=${type}`),
  operators: () => request<OperatorList>("/api/operadores"),
  registerEntry: (body: {
    placa: string;
    codigo_celda: string;
    id_operador: number;
  }) =>
    request<EntryResult>("/api/entradas", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  activeStays: () => request<ActiveStays>("/api/estancias/activas"),
  registerExit: (body: { placa: string; id_operador: number }) =>
    request<ExitResult>("/api/salidas", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  status: () => request<ParkingStatus>("/api/parqueadero/estado"),
};
