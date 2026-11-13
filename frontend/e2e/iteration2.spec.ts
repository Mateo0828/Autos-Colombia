import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

const MODE = process.env.E2E_MODE ?? "mock";
const SHOTS =
  process.env.CAPTURES_DIR ??
  path.resolve(__dirname, "../../../CLAUDE_FILES/AutosColombia_intercambio/informes/capturas");

// Demo credentials: the mock ones are invented here; for [real] runs pass the
// backend's seed values (README, "solo desarrollo") through the environment.
const ADMIN = {
  user: process.env.E2E_ADMIN_USER ?? "admin",
  pass: process.env.E2E_ADMIN_PASS ?? "Admin12345",
};
const OPER = {
  user: process.env.E2E_OPER_USER ?? "operador1",
  pass: process.env.E2E_OPER_PASS ?? "Operador123",
};

const shot = (page: Page, name: string) =>
  page.screenshot({ path: path.join(SHOTS, `f02_${MODE}_${name}.png`) });

async function login(page: Page, u: { user: string; pass: string }) {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill(u.user);
  await page.getByLabel("Contraseña").fill(u.pass);
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page).toHaveURL(/\/entrada/);
}

async function checkPlate(page: Page, plate: string) {
  await page.goto("/entrada");
  await page.getByLabel("Placa").fill(plate);
  await page.getByRole("button", { name: "Consultar vehículo" }).click();
}

test("T-01 login válido de administrador y menú completo", async ({ page }) => {
  await login(page, ADMIN);
  await expect(page.getByTestId("session-box")).toContainText("Administrador");
  for (const l of ["Usuarios", "Celdas", "Clientes y vehículos", "Registrar cliente y vehículo"])
    await expect(page.getByRole("link", { name: l })).toBeVisible();
  await shot(page, "01_login_admin_entrada");
});

test("T-02 credenciales incorrectas y campos vacíos", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page.getByText("Ingresa tu usuario.")).toBeVisible();
  await expect(page.getByText("Ingresa tu contraseña.")).toBeVisible();
  await page.getByLabel("Usuario").fill("admin");
  await page.getByLabel("Contraseña").fill("incorrecta999");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page.getByText("Usuario o contraseña incorrectos.")).toBeVisible();
  await expect(page).toHaveURL(/\/login/);
  await shot(page, "02_login_error");
});

test("T-03 sin sesión se redirige a /login", async ({ page }) => {
  await page.goto("/usuarios");
  await expect(page).toHaveURL(/\/login/);
});

test("T-04 operador: menú reducido y sin acceso a rutas de administrador", async ({ page }) => {
  await login(page, OPER);
  await expect(page.getByTestId("session-box")).toContainText("Operador");
  for (const l of ["Usuarios", "Celdas", "Clientes y vehículos"])
    await expect(page.getByRole("link", { name: l })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Registrar cliente y vehículo" })).toBeVisible();
  for (const route of ["/usuarios", "/clientes", "/celdas"]) {
    await page.goto(route);
    await expect(page.getByText("No tienes permiso")).toBeVisible();
  }
  await shot(page, "03_operador_sin_permiso");
});

test("T-05 administrador crea un operador y valida el formulario", async ({ page }) => {
  await login(page, ADMIN);
  await page.getByRole("link", { name: "Usuarios" }).click();
  await page.getByRole("button", { name: "Nuevo usuario" }).click();
  const form = page.getByRole("form", { name: "Nuevo usuario" });
  await form.getByRole("button", { name: "Guardar" }).click();
  await expect(form.getByText("El nombre es obligatorio.")).toBeVisible();
  await expect(form.getByText("Selecciona un rol.")).toBeVisible();
  await form.getByLabel("Nombre").fill("Operador Prueba");
  await form.getByLabel("Usuario").fill("Prueba1");
  await form.getByLabel("Rol").selectOption("OPERADOR");
  await form.getByLabel("Contraseña").fill("corta");
  await form.getByRole("button", { name: "Guardar" }).click();
  await expect(form.getByText("La contraseña debe tener al menos 8 caracteres.")).toBeVisible();
  await form.getByLabel("Contraseña").fill("ClaveSegura1");
  await form.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByTestId("user-row-prueba1")).toContainText("Operador Prueba");
  await shot(page, "04_usuarios_creado");

  // Duplicate (server-side 409) — normalised to lowercase.
  await page.getByRole("button", { name: "Nuevo usuario" }).first().click();
  const form2 = page.getByRole("form", { name: "Nuevo usuario" });
  await form2.getByLabel("Nombre").fill("Otro");
  await form2.getByLabel("Usuario").fill("PRUEBA1");
  await form2.getByLabel("Rol").selectOption("OPERADOR");
  await form2.getByLabel("Contraseña").fill("ClaveSegura1");
  await form2.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByRole("alert").filter({ hasText: /registrad|existe|duplicad/i })).toBeVisible();
});

test("T-06 inactivar usuario con confirmación y no inactivarse a sí mismo", async ({ page }) => {
  await login(page, ADMIN);
  await page.goto("/usuarios");
  await expect(page.getByRole("button", { name: `Inactivar ${ADMIN.user}` })).toBeDisabled();
  await page.getByRole("button", { name: "Inactivar operador3" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Inactivar" }).click();
  await expect(page.getByTestId("user-row-operador3")).toContainText("INACTIVO");
  await shot(page, "05_usuario_inactivado");
});

test("T-07 registro de cliente y vehículo desde Entrada (no registrado)", async ({ page }) => {
  await login(page, OPER);
  await checkPlate(page, "zzz999");
  await expect(page.getByText("El vehículo no se encuentra registrado.")).toBeVisible();
  await page.getByRole("link", { name: "Registrar cliente y vehículo" }).last().click();
  await expect(page).toHaveURL(/\/registro\?placa=ZZZ999/);
  await expect(page.getByLabel("Placa")).toHaveValue("ZZZ999");

  const doc = `9${Date.now().toString().slice(-8)}`;
  await page.getByRole("button", { name: "Registrar cliente y vehículo" }).click();
  await expect(page.getByText("El documento es obligatorio.")).toBeVisible();
  await expect(page.getByText("Selecciona el tipo de vehículo.")).toBeVisible();

  await page.getByLabel("Documento").fill(doc);
  await page.getByLabel("Nombre completo").fill("Cliente de Prueba");
  await page.getByLabel("Tipo de vehículo").selectOption("AUTOMOVIL");
  await page.getByLabel("Marca").fill("Kia");
  await page.getByLabel("Color").fill("Verde");
  await page.getByRole("button", { name: "Registrar cliente y vehículo" }).click();
  await expect(page.getByRole("status")).toContainText(/registrados correctamente/i);
  await shot(page, "06_registro_exitoso");

  // Same plate again -> 409
  await page.goto("/registro?placa=ZZZ999");
  await page.getByLabel("Documento").fill(doc);
  await page.getByLabel("Nombre completo").fill("Cliente de Prueba");
  await page.getByLabel("Tipo de vehículo").selectOption("AUTOMOVIL");
  await page.getByLabel("Marca").fill("Kia");
  await page.getByLabel("Color").fill("Verde");
  await page.getByRole("button", { name: "Registrar cliente y vehículo" }).click();
  await expect(page.getByRole("alert").filter({ hasText: /registrad/i })).toBeVisible();

  // Now the vehicle can be consulted for entry.
  await checkPlate(page, "ZZZ999");
  await expect(page.getByText("Kia")).toBeVisible();
});

test("T-08 administrador modifica cliente y vehículo", async ({ page }) => {
  await login(page, ADMIN);
  await page.getByRole("link", { name: "Clientes y vehículos" }).click();
  await expect(page.getByRole("heading", { name: "Clientes y vehículos" })).toBeVisible();
  await page.getByLabel("Placa").fill("ABC123");
  await page.getByRole("button", { name: "Buscar" }).click();
  const clientForm = page.getByRole("form", { name: "Datos del cliente" });
  await clientForm.getByLabel("Nombre completo").fill("Carlos Rodriguez Editado");
  await clientForm.getByRole("button", { name: "Guardar cliente" }).click();
  await expect(page.getByRole("status")).toContainText(/actualizado/i);
  const vehicleForm = page.getByRole("form", { name: "Vehículo ABC123" });
  await vehicleForm.getByLabel("Color").fill("Rojo");
  await vehicleForm.getByRole("button", { name: "Guardar vehículo" }).click();
  await expect(page.getByRole("status")).toContainText(/actualizado/i);
  await shot(page, "07_clientes_modificado");
});

test("T-09 celdas: filtros, deshabilitar, entrada sin celda deshabilitada, habilitar", async ({ page }) => {
  await login(page, ADMIN);
  await page.getByRole("link", { name: "Celdas" }).click();
  await expect(page.getByTestId("cells-count")).toContainText("80");
  await page.getByLabel("Tipo").selectOption("MOTO");
  await expect(page.getByTestId("cells-count")).toContainText("10");
  await page.getByLabel("Tipo").selectOption("");
  await page.getByLabel("Buscar por código").fill("c05");
  await expect(page.getByTestId("cells-count")).toContainText("1 celdas");
  await shot(page, "08_celdas_filtro");

  await page.getByRole("button", { name: "Deshabilitar celda C05" }).click();
  await expect(page.getByRole("dialog")).toContainText("C05");
  await page.getByRole("dialog").getByRole("button", { name: "Deshabilitar" }).click();
  await expect(page.getByTestId("cell-row-C05")).toContainText("Fuera de servicio");
  await shot(page, "09_celda_deshabilitada");

  // Entry must not offer C05.
  await checkPlate(page, "ABC123");
  await expect(page.getByRole("button", { name: "C04", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "C05", exact: true })).toHaveCount(0);
  await shot(page, "10_entrada_sin_celda_deshabilitada");

  // Enable again.
  await page.goto("/celdas");
  await page.getByLabel("Buscar por código").fill("C05");
  await page.getByRole("button", { name: "Habilitar celda C05" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Habilitar" }).click();
  await expect(page.getByTestId("cell-row-C05")).toContainText("Disponible");
});

test("T-10 entrada con operador de la sesión; celda ocupada no se puede deshabilitar", async ({ page }) => {
  await login(page, OPER);
  await checkPlate(page, "ABC123");
  await expect(page.locator("select")).toHaveCount(0);
  await expect(page.getByTestId("operator-label")).toContainText("Operador:");
  await page.getByRole("button", { name: "C01", exact: true }).click();
  await page.getByRole("button", { name: "Registrar entrada" }).click();
  await expect(page.getByRole("status")).toContainText("Entrada registrada. Celda C01 ocupada");
  await shot(page, "11_entrada_exitosa");

  // Salida also without operator selector.
  await page.goto("/salida?placa=ABC123");
  await expect(page.getByTestId("operator-label")).toBeVisible();
  await expect(page.locator("select")).toHaveCount(0);
  await shot(page, "12_salida_operador_sesion");

  // Admin tries to disable the occupied cell.
  await page.getByRole("button", { name: "Cerrar sesión" }).first().click();
  await expect(page).toHaveURL(/\/login/);
  await login(page, ADMIN);
  await page.goto("/celdas");
  await page.getByLabel("Buscar por código").fill("C01");
  await page.getByRole("button", { name: "Deshabilitar celda C01" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Deshabilitar" }).click();
  await expect(page.getByRole("alert").filter({ hasText: /ocupada/i })).toBeVisible();
  await shot(page, "13_celda_ocupada_409");
});

test("T-11 estado muestra celdas fuera de servicio", async ({ page }) => {
  await login(page, ADMIN);
  await page.goto("/celdas");
  await page.getByLabel("Buscar por código").fill("M10");
  await page.getByRole("button", { name: "Deshabilitar celda M10" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Deshabilitar" }).click();
  await expect(page.getByTestId("cell-row-M10")).toContainText("Fuera de servicio");
  await page.getByRole("link", { name: "Estado del parqueadero" }).click();
  await expect(page.getByText("Fuera de servicio").first()).toBeVisible();
  await shot(page, "14_estado_fuera_de_servicio");
  await page.goto("/celdas");
  await page.getByLabel("Buscar por código").fill("M10");
  await page.getByRole("button", { name: "Habilitar celda M10" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Habilitar" }).click();
});

test("T-12 cerrar sesión limpia el token y bloquea las rutas", async ({ page }) => {
  await login(page, ADMIN);
  expect(await page.evaluate(() => sessionStorage.getItem("ac.token"))).toBeTruthy();
  await page.getByRole("button", { name: "Cerrar sesión" }).first().click();
  await expect(page).toHaveURL(/\/login/);
  expect(await page.evaluate(() => sessionStorage.getItem("ac.token"))).toBeNull();
  await page.goto("/entrada");
  await expect(page).toHaveURL(/\/login/);
  await shot(page, "15_logout");
});

// ---------------------------------------------------------------------------
// Server-side cases. They need the real backend (the mock is not evidence), so
// they run only with E2E_MODE=real. They call the API directly.
// ---------------------------------------------------------------------------
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:5000";

async function apiLogin(
  request: import("@playwright/test").APIRequestContext,
  u: { user: string; pass: string },
) {
  const res = await request.post(`${API}/api/auth/login`, {
    data: { usuario: u.user, password: u.pass },
  });
  expect(res.status()).toBe(200);
  return (await res.json()).token as string;
}
const bearer = (t: string) => ({ Authorization: `Bearer ${t}` });

test.describe("[real] casos de servidor", () => {
  test.skip(MODE !== "real", "requiere el backend real");

  test("T-13 token revocado tras logout responde 401; sin token 401", async ({ request }) => {
    const t = await apiLogin(request, ADMIN);
    expect((await request.get(`${API}/api/auth/me`, { headers: bearer(t) })).status()).toBe(200);
    expect((await request.post(`${API}/api/auth/logout`, { headers: bearer(t) })).status()).toBe(200);
    expect((await request.get(`${API}/api/auth/me`, { headers: bearer(t) })).status()).toBe(401);
    expect((await request.get(`${API}/api/usuarios`, { headers: bearer(t) })).status()).toBe(401);
    expect((await request.get(`${API}/api/usuarios`)).status()).toBe(401);
  });

  test("T-14 dos sesiones simultáneas del mismo usuario; cerrar una no cierra la otra", async ({ request }) => {
    const a = await apiLogin(request, OPER);
    const b = await apiLogin(request, OPER);
    expect(a).not.toBe(b);
    expect((await request.get(`${API}/api/auth/me`, { headers: bearer(a) })).status()).toBe(200);
    expect((await request.get(`${API}/api/auth/me`, { headers: bearer(b) })).status()).toBe(200);
    await request.post(`${API}/api/auth/logout`, { headers: bearer(a) });
    expect((await request.get(`${API}/api/auth/me`, { headers: bearer(a) })).status()).toBe(401);
    expect((await request.get(`${API}/api/auth/me`, { headers: bearer(b) })).status()).toBe(200);
    await request.post(`${API}/api/auth/logout`, { headers: bearer(b) });
  });

  test("T-15 operador recibe 403 en endpoints de administrador", async ({ request }) => {
    const t = await apiLogin(request, OPER);
    for (const [method, url] of [
      ["get", "/api/usuarios"],
      ["get", "/api/celdas"],
      ["get", "/api/clientes/1"],
      ["patch", "/api/celdas/C60/deshabilitar"],
    ] as const) {
      const res = await request[method](`${API}${url}`, { headers: bearer(t) });
      expect(res.status(), `${method} ${url}`).toBe(403);
    }
    await request.post(`${API}/api/auth/logout`, { headers: bearer(t) });
  });

  test("T-16 celda ocupada: deshabilitar responde 409 y la celda sigue OCUPADA", async ({ request }) => {
    const op = await apiLogin(request, OPER);
    // GHI789 enters C03 (ABC123 may already be in C01 from T-10).
    const entry = await request.post(`${API}/api/entradas`, {
      headers: bearer(op),
      data: { placa: "GHI789", codigo_celda: "C03" },
    });
    expect([201, 400]).toContain(entry.status());
    const admin = await apiLogin(request, ADMIN);
    const res = await request.patch(`${API}/api/celdas/C03/deshabilitar`, { headers: bearer(admin) });
    expect(res.status()).toBe(409);
    expect((await res.json()).mensaje).toMatch(/ocupada/i);
    const cells = await (
      await request.get(`${API}/api/celdas?q=C03`, { headers: bearer(admin) })
    ).json();
    expect(cells.celdas[0].estado).toBe("OCUPADA");
    // clean up so the base is left usable
    await request.post(`${API}/api/salidas`, { headers: bearer(op), data: { placa: "GHI789" } });
    await request.post(`${API}/api/auth/logout`, { headers: bearer(op) });
    await request.post(`${API}/api/auth/logout`, { headers: bearer(admin) });
  });

  test("T-17 UI: tras logout, el token viejo ya no sirve y la placa no se edita (D-26)", async ({ page, request }) => {
    await login(page, ADMIN);
    const token = await page.evaluate(() => sessionStorage.getItem("ac.token"));
    expect(token).toBeTruthy();
    await page.getByRole("button", { name: "Cerrar sesión" }).first().click();
    await expect(page).toHaveURL(/\/login/);
    expect((await request.get(`${API}/api/auth/me`, { headers: bearer(token!) })).status()).toBe(401);

    await login(page, ADMIN);
    await page.goto("/clientes");
    await page.getByLabel("Placa").fill("DEF456");
    await page.getByRole("button", { name: "Buscar" }).click();
    const vehicleForm = page.getByRole("form", { name: "Vehículo DEF456" });
    await expect(vehicleForm.getByLabel("Placa")).toHaveAttribute("readonly", "");
    await shot(page, "16_clientes_placa_inmutable");
  });
});
