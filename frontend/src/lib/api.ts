import type {
  ActiveStays,
  AvailableCells,
  CellChange,
  CellList,
  CellState,
  CellType,
  ClientResult,
  ClientUpdateResult,
  EntryResult,
  EntryValidation,
  ExitResult,
  LoginResult,
  MeResult,
  MessageResult,
  ParkingStatus,
  RegistrationResult,
  Role,
  UserList,
  UserResult,
  UserStatus,
  VehicleResult,
  VehicleType,
} from "@/types/api";
import { mockRequest } from "@/lib/mock";
import { clearSession, getToken } from "@/lib/session";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:5000";
// [mock] mode: no network, in-memory data. Only for development without backend.
export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

export const CONNECTION_ERROR = "No se pudo conectar con el servidor";

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public status: number | null,
  ) {
    super(message);
  }
}

let unauthorizedHandler: (() => void) | null = null;

/** The auth provider registers what to do when a request answers 401. */
export function setUnauthorizedHandler(fn: (() => void) | null) {
  unauthorizedHandler = fn;
}

interface RequestOptions extends RequestInit {
  /** Login does not carry a token and its 401 must not end a session. */
  public?: boolean;
}

async function rawRequest(
  path: string,
  init: RequestOptions,
): Promise<{ status: number; ok: boolean; data: unknown }> {
  const token = init.public ? null : getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  if (USE_MOCK) {
    const r = await mockRequest(path, { ...init, headers });
    return { status: r.status, ok: r.status < 400, data: r.data };
  }

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, { ...init, cache: "no-store", headers });
  } catch {
    throw new ApiRequestError(CONNECTION_ERROR, null);
  }
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    // non-JSON body handled by the caller
  }
  return { status: res.status, ok: res.ok, data };
}

async function request<T>(path: string, init: RequestOptions = {}): Promise<T> {
  const sentToken = init.public ? null : getToken();
  const { status, ok, data } = await rawRequest(path, init);
  if (!ok) {
    const msg =
      data && typeof data === "object" && "mensaje" in data
        ? String((data as { mensaje: unknown }).mensaje)
        : "Ocurrió un error inesperado en el servidor.";
    // Only a 401 for the CURRENT session ends it; a late 401 that arrives after
    // an intentional logout (token already cleared) must not redirect again.
    if (status === 401 && sentToken && getToken() === sentToken) {
      clearSession();
      unauthorizedHandler?.();
    }
    throw new ApiRequestError(msg, status);
  }
  return data as T;
}

function json(method: string, body?: unknown): RequestOptions {
  return { method, body: body === undefined ? undefined : JSON.stringify(body) };
}

export function errorMessage(e: unknown): string {
  return e instanceof Error ? e.message : CONNECTION_ERROR;
}

export interface NewUserBody {
  nombre: string;
  usuario: string;
  password: string;
  rol: Role;
}

export interface EditUserBody {
  nombre: string;
  rol?: Role;
  password?: string;
}

/** D-26: flat body. */
export interface RegistrationBody {
  documento: string;
  nombre: string;
  placa: string;
  marca: string;
  color: string;
  tipo_vehiculo: VehicleType;
}

export interface CellFilters {
  estado?: CellState | "";
  tipo?: CellType | "";
  q?: string;
}

export const api = {
  // Authentication
  login: (usuario: string, password: string) =>
    request<LoginResult>("/api/auth/login", {
      ...json("POST", { usuario, password }),
      public: true,
    }),
  logout: () => request<MessageResult>("/api/auth/logout", json("POST")),
  me: () => request<MeResult>("/api/auth/me"),

  // Users (administrator)
  users: () => request<UserList>("/api/usuarios"),
  createUser: (body: NewUserBody) =>
    request<UserResult>("/api/usuarios", json("POST", body)),
  updateUser: (id: number, body: EditUserBody) =>
    request<UserResult>(`/api/usuarios/${id}`, json("PUT", body)),
  setUserStatus: (id: number, estado: UserStatus) =>
    request<UserResult>(`/api/usuarios/${id}/estado`, json("PATCH", { estado })),

  // Clients and vehicles
  register: (body: RegistrationBody) =>
    request<RegistrationResult>("/api/registros", json("POST", body)),
  client: (id: number) => request<ClientResult>(`/api/clientes/${id}`),
  updateClient: (id: number, body: { documento: string; nombre: string }) =>
    request<ClientUpdateResult>(`/api/clientes/${id}`, json("PUT", body)),
  updateVehicle: (
    plate: string,
    body: {
      marca: string;
      color: string;
      tipo_vehiculo: VehicleType;
      estado_mensualidad: "ACTIVA" | "INACTIVA";
    },
  ) =>
    request<VehicleResult>(
      `/api/vehiculos/${encodeURIComponent(plate)}`,
      json("PUT", body),
    ),

  // Cells
  cells: (f: CellFilters = {}) => {
    const p = new URLSearchParams();
    if (f.estado) p.set("estado", f.estado);
    if (f.tipo) p.set("tipo", f.tipo);
    if (f.q?.trim()) p.set("q", f.q.trim());
    const qs = p.toString();
    return request<CellList>(`/api/celdas${qs ? `?${qs}` : ""}`);
  },
  disableCell: (code: string) =>
    request<CellChange>(
      `/api/celdas/${encodeURIComponent(code)}/deshabilitar`,
      json("PATCH"),
    ),
  enableCell: (code: string) =>
    request<CellChange>(
      `/api/celdas/${encodeURIComponent(code)}/habilitar`,
      json("PATCH"),
    ),

  // Iteration 1 (operator now comes from the token, D-21)
  validateEntry: (plate: string) =>
    request<EntryValidation>(
      `/api/vehiculos/${encodeURIComponent(plate)}/validar-ingreso`,
    ),
  availableCells: (type: VehicleType) =>
    request<AvailableCells>(`/api/celdas/disponibles?tipo_vehiculo=${type}`),
  registerEntry: (body: { placa: string; codigo_celda: string }) =>
    request<EntryResult>("/api/entradas", json("POST", body)),
  activeStays: () => request<ActiveStays>("/api/estancias/activas"),
  registerExit: (body: { placa: string }) =>
    request<ExitResult>("/api/salidas", json("POST", body)),
  status: () => request<ParkingStatus>("/api/parqueadero/estado"),
};
