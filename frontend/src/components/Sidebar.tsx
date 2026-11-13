"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Car,
  Contact,
  LayoutGrid,
  LogIn,
  LogOut,
  ParkingSquare,
  Power,
  UserPlus,
  Users,
} from "lucide-react";
import type { Role } from "@/types/api";
import { useAuth } from "./AuthContext";

const ITEMS: {
  href: string;
  label: string;
  icon: typeof Car;
  role?: Role;
}[] = [
  { href: "/entrada", label: "Entrada", icon: LogIn },
  { href: "/salida", label: "Salida", icon: LogOut },
  { href: "/vehiculos-dentro", label: "Vehículos dentro", icon: Car },
  { href: "/estado", label: "Estado del parqueadero", icon: LayoutGrid },
  { href: "/registro", label: "Registrar cliente y vehículo", icon: UserPlus },
  { href: "/clientes", label: "Clientes y vehículos", icon: Contact, role: "ADMINISTRADOR" },
  { href: "/celdas", label: "Celdas", icon: ParkingSquare, role: "ADMINISTRADOR" },
  { href: "/usuarios", label: "Usuarios", icon: Users, role: "ADMINISTRADOR" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const items = ITEMS.filter((i) => !i.role || i.role === user?.rol);
  return (
    <nav
      aria-label="Navegación principal"
      className="sticky top-0 flex h-screen w-[104px] shrink-0 flex-col overflow-y-auto border-r border-line"
    >
      <div className="flex h-[108px] shrink-0 items-center justify-center border-b border-line text-2xl font-extrabold text-accent">
        AC
      </div>
      <ul className="mt-7 flex flex-col items-center gap-3">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <li key={href} className="relative">
              {active && (
                <span className="absolute -left-[21px] top-2 h-[42px] w-[3px] rounded-r bg-accent" />
              )}
              <Link
                href={href}
                title={label}
                aria-label={label}
                aria-current={active ? "page" : undefined}
                className={`flex h-14 w-14 items-center justify-center rounded-2xl border transition ${
                  active
                    ? "border-accent/40 bg-card text-accent"
                    : "border-transparent text-muted hover:bg-card/60 hover:text-foreground"
                }`}
              >
                <Icon size={22} strokeWidth={1.6} />
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="mt-auto flex flex-col items-center gap-1 pb-6 pt-6">
        <button
          type="button"
          onClick={() => logout()}
          title="Cerrar sesión"
          aria-label="Cerrar sesión"
          className="flex h-14 w-14 items-center justify-center rounded-2xl border border-transparent text-muted transition hover:bg-danger/10 hover:text-danger"
        >
          <Power size={22} strokeWidth={1.6} />
        </button>
        <span className="text-[10px] text-muted">Cerrar sesión</span>
      </div>
    </nav>
  );
}
