"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGrid, LogIn, LogOut, Car } from "lucide-react";

const ITEMS = [
  { href: "/entrada", label: "Entrada", icon: LogIn },
  { href: "/salida", label: "Salida", icon: LogOut },
  { href: "/vehiculos-dentro", label: "Vehículos dentro", icon: Car },
  { href: "/estado", label: "Estado del parqueadero", icon: LayoutGrid },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Navegación principal"
      className="sticky top-0 flex h-screen w-[104px] shrink-0 flex-col border-r border-line"
    >
      <div className="flex h-[108px] items-center justify-center border-b border-line text-2xl font-extrabold text-accent">
        AC
      </div>
      <ul className="mt-7 flex flex-col items-center gap-3">
        {ITEMS.map(({ href, label, icon: Icon }) => {
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
    </nav>
  );
}
