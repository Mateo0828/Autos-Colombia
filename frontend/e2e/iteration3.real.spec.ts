import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import path from "node:path";

// Iteration 3 (payments) against the REAL backend (feature/i3-backend, D-39). Results are [real].
// Run with E2E_MODE=real, E2E_BASE_URL (a build made WITHOUT NEXT_PUBLIC_USE_MOCK) and the E2E_* credentials.
// Seed plates are only READ; every payment is made on a plate created by the test itself.
const MODE = process.env.E2E_MODE ?? "mock";
test.skip(MODE !== "real", "requiere el backend real");

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:5000";
const SHOTS =
  process.env.CAPTURES_DIR ??
  path.resolve(__dirname, "../../../CLAUDE_FILES/AutosColombia_intercambio/informes/capturas");

const ADMIN = { user: process.env.E2E_ADMIN_USER ?? "", pass: process.env.E2E_ADMIN_PASS ?? "" };
const OPER = { user: process.env.E2E_OPER_USER ?? "", pass: process.env.E2E_OPER_PASS ?? "" };

const shot = (page: Page, name: string) =>
  page.screenshot({ path: path.join(SHOTS, `f06_real_${name}.png`), fullPage: true });

// ---- helpers ----
const bearer = (t: string) => ({ Authorization: `Bearer ${t}` });
const dmy = (iso: string) => iso.split("-").reverse().join("/");

let seq = 0;
/** Unique plate / document per run, so the suite never collides with earlier runs. */
function unique(prefix: string) {
  seq += 1;
  const stamp = (Date.now() % 36 ** 4).toString(36).toUpperCase().padStart(4, "0");
  return { plate: `${prefix}${stamp}${seq}`.slice(0, 10), doc: `9${Date.now() % 1e9}${seq}`.slice(0, 15) };
}

async function apiLogin(request: APIRequestContext, u: { user: string; pass: string }) {
  const res = await request.post(`${API}/api/auth/login`, { data: { usuario: u.user, password: u.pass } });
  expect(res.status()).toBe(200);
  return (await res.json()) as { token: string; usuario: { nombre: string; usuario: string } };
}

async function createVehicle(request: APIRequestContext, type: "AUTOMOVIL" | "MOTO" = "AUTOMOVIL", prefix = "RP") {
  const { token } = await apiLogin(request, OPER);
  const { plate, doc } = unique(prefix);
  const res = await request.post(`${API}/api/registros`, {
    headers: bearer(token),
    data: { documento: doc, nombre: "Cliente Prueba F06", placa: plate, marca: "Mazda", color: "Rojo", tipo_vehiculo: type },
  });
  expect(res.status()).toBe(201);
  return plate;
}

async function apiGet(request: APIRequestContext, route: string) {
  const { token } = await apiLogin(request, ADMIN);
  const res = await request.get(`${API}${route}`, { headers: bearer(token) });
  return { status: res.status(), body: await res.json() };
}

async function login(page: Page, u: { user: string; pass: string }) {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill(u.user);
  await page.getByLabel("Contraseña").fill(u.pass);
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page).toHaveURL(/\/entrada/);
}

async function consult(page: Page, plate: string) {
  await page.goto("/pagos");
  await expect(page.getByRole("heading", { name: "Consultar mensualidad" })).toBeVisible();
  const button = page.getByRole("button", { name: "Consultar", exact: true });
  await expect(async () => {
    await page.getByLabel("Placa").fill(plate);
    await expect(button).toBeEnabled({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  await button.click();
  await expect(page.getByRole("heading", { name: `Vehículo ${plate}` })).toBeVisible();
}

const confirm = (page: Page) => page.getByRole("dialog").getByRole("button", { name: "Confirmar pago" });

/** Fills the dialog date and waits for the server's projection for THAT date. */
async function pickDate(page: Page, iso: string) {
  await page.getByRole("dialog").getByLabel("Fecha del pago").fill(iso);
  await expect(confirm(page)).toBeEnabled();
}

const isoDaysAgo = (n: number) => {
  const d = new Date();
  d.setDate(d.getDate() - n);
  const p = (x: number) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
};

// ---- cases ----

test("R-01 login de administrador y de operador; ambos ven «Pagos»", async ({ page, browser }) => {
  await login(page, ADMIN);
  await expect(page.getByRole("link", { name: "Pagos" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Clientes y vehículos" })).toBeVisible();
  await shot(page, "01_login_admin");
  const ctx = await browser.newContext();
  const p2 = await ctx.newPage();
  await login(p2, OPER);
  await expect(p2.getByRole("link", { name: "Pagos" })).toBeVisible();
  await expect(p2.getByRole("link", { name: "Clientes y vehículos" })).toHaveCount(0);
  await ctx.close();
});

test("R-02 primer pago y renovación anticipada sobre una placa creada por la prueba", async ({ page, request }) => {
  const plate = await createVehicle(request);
  const { usuario } = await apiLogin(request, OPER);
  await login(page, OPER);
  await consult(page, plate);
  const card = page.getByTestId("monthly-card");
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA");
  await expect(card).toContainText("$250.000");
  await expect(card).toContainText("Pagos registrados0");
  await shot(page, "02_primer_pago_tarjeta");

  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  await expect(page.getByRole("dialog").getByLabel("Valor")).toHaveValue("$250.000");
  await expect(page.getByTestId("resulting-state")).toHaveText("ACTIVA");
  await expect(page.getByTestId("advance-notice")).toHaveCount(0);
  const next1 = (await page.getByTestId("next-cutoff").textContent())!;
  await shot(page, "03_primer_pago_ventana");
  await confirm(page).click();

  const result = page.getByTestId("payment-result");
  await expect(result).toContainText("Pago registrado correctamente.");
  await expect(result).toContainText(`Nueva fecha de corte ${next1}`);
  await expect(result).toContainText(`Registrado por ${usuario.nombre}`);
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad ACTIVA");
  await expect(card).toContainText("Pagos registrados1");
  await shot(page, "04_primer_pago_resultado");

  // Cross-check with what the server holds.
  const m1 = await apiGet(request, `/api/mensualidades/${plate}`);
  expect(m1.body.estado_mensualidad).toBe("ACTIVA");
  expect(dmy(m1.body.fecha_corte)).toBe(next1);
  await expect(card).toContainText(`Día de corte${m1.body.dia_corte}`);

  // Early renewal: the current cut-off is after today.
  await page.getByRole("button", { name: "Renovar mensualidad" }).click();
  await expect(page.getByTestId("advance-notice")).toContainText("Pago anticipado");
  await expect(page.getByTestId("cutoff-day")).toHaveText(String(m1.body.dia_corte));
  const next2 = (await page.getByTestId("next-cutoff").textContent())!;
  expect(next2).not.toBe(next1);
  await shot(page, "05_renovacion_anticipada_ventana");
  await confirm(page).click();
  await expect(page.getByTestId("payment-result")).toContainText(`Nueva fecha de corte ${next2}`);
  await expect(page.getByTestId("payment-warning")).toHaveCount(0);
  await expect(card).toContainText("Pagos registrados2");
  const m2 = await apiGet(request, `/api/mensualidades/${plate}`);
  expect(dmy(m2.body.fecha_corte)).toBe(next2);
  expect(m2.body.num_pagos).toBe(2);
  await shot(page, "06_renovacion_anticipada_resultado");
});

test("R-03 pago tardío: al cambiar la fecha se vuelve a consultar; advertencia y mensualidad INACTIVA", async ({ page, request }) => {
  const plate = await createVehicle(request);
  await login(page, OPER);
  await consult(page, plate);
  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  await expect(page.getByTestId("resulting-state")).toHaveText("ACTIVA");
  await expect(page.getByTestId("projection-warning")).toHaveCount(0);

  const old = isoDaysAgo(70);
  await pickDate(page, old);
  await expect(page.getByTestId("resulting-state")).toHaveText("INACTIVA");
  await expect(page.getByTestId("projection-warning")).toBeVisible();
  const warning = (await page.getByTestId("projection-warning").textContent())!;
  const proj = await apiGet(request, `/api/mensualidades/${plate}?fecha_pago=${old}`);
  expect(dmy(proj.body.proximo_pago.periodo_fin)).toBe(await page.getByTestId("next-cutoff").textContent());
  expect(warning).toBe(proj.body.proximo_pago.advertencia);
  await shot(page, "07_pago_tardio_ventana");
  await confirm(page).click();
  await expect(page.getByTestId("payment-result")).toContainText("Estado INACTIVA");
  await expect(page.getByTestId("payment-warning")).toContainText(warning);
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA");
  await shot(page, "08_pago_tardio_resultado");

  // Late renewal on top: starts at the previous cut-off and may stay INACTIVA with a warning.
  await page.getByRole("button", { name: "Renovar mensualidad" }).click();
  await expect(page.getByTestId("advance-notice")).toHaveCount(0);
  await confirm(page).click();
  await expect(page.getByTestId("payment-result")).toContainText("Pago registrado correctamente.");
  await expect(page.getByTestId("monthly-card")).toContainText("Pagos registrados2");
});

test("R-04 JKL321 (semilla, solo lectura): vencida; el servidor proyecta la renovación y su estado", async ({ page, request }) => {
  await login(page, OPER);
  await consult(page, "JKL321");
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA");
  const srv = await apiGet(request, "/api/mensualidades/JKL321");
  await page.getByRole("button", { name: "Renovar mensualidad" }).click();
  await expect(page.getByTestId("resulting-state")).toHaveText(srv.body.proximo_pago.estado_resultante);
  await expect(page.getByTestId("next-cutoff")).toHaveText(dmy(srv.body.proximo_pago.periodo_fin));
  if (srv.body.proximo_pago.advertencia)
    await expect(page.getByTestId("projection-warning")).toHaveText(srv.body.proximo_pago.advertencia);
  else await expect(page.getByTestId("projection-warning")).toHaveCount(0);
  await shot(page, "09_jkl321_renovacion_proyeccion");
  await page.getByRole("dialog").getByRole("button", { name: "Cancelar" }).click(); // the seed plate is NOT paid
});

test("R-05 409 con dos sesiones: la segunda confirma con un corte desactualizado", async ({ browser, request }) => {
  const plate = await createVehicle(request);
  // First payment through the API so that both sessions share a renewal (corte_esperado = a date).
  const { token } = await apiLogin(request, OPER);
  const first = await request.post(`${API}/api/pagos`, {
    headers: bearer(token),
    data: { placa: plate, fecha_pago: isoDaysAgo(0), corte_esperado: null },
  });
  expect(first.status()).toBe(201);

  const open = async (u: typeof OPER) => {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await login(page, u);
    await consult(page, plate);
    await page.getByRole("button", { name: "Renovar mensualidad" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    return { ctx, page };
  };
  const A = await open(OPER);
  const B = await open(ADMIN);
  try {
    await expect(A.page.getByTestId("monthly-card")).toContainText("Pagos registrados1");
    await confirm(A.page).click(); // A wins
    await expect(A.page.getByTestId("payment-result")).toContainText("Pago registrado correctamente.");

    await shot(B.page, "10_dos_sesiones_B_antes");
    await confirm(B.page).click(); // B still holds the old corte_esperado
    await expect(B.page.getByRole("alert").filter({ hasText: "La mensualidad ya fue actualizada; consulte de nuevo." })).toBeVisible();
    await expect(B.page.getByRole("dialog")).toHaveCount(0);
    await expect(B.page.getByTestId("payment-result")).toHaveCount(0);
    await expect(B.page.getByTestId("monthly-card")).toContainText("Pagos registrados2"); // reloaded automatically
    await shot(B.page, "11_dos_sesiones_B_409");

    // No automatic retry happened: the server holds exactly 2 payments. B must confirm again.
    expect((await apiGet(request, `/api/vehiculos/${plate}/pagos`)).body.cantidad).toBe(2);
    await B.page.getByRole("button", { name: "Renovar mensualidad" }).click();
    await confirm(B.page).click();
    await expect(B.page.getByTestId("payment-result")).toContainText("Pago registrado correctamente.");
    expect((await apiGet(request, `/api/vehiculos/${plate}/pagos`)).body.cantidad).toBe(3);
  } finally {
    await A.ctx.close();
    await B.ctx.close();
  }
});

test("R-06 422: fecha futura bloqueada en el cliente y rechazada por el servidor; campos extra", async ({ page, request }) => {
  const plate = await createVehicle(request);
  await login(page, OPER);
  await consult(page, plate);
  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  const dialog = page.getByRole("dialog");
  const tomorrow = await page.evaluate(() => {
    const d = new Date();
    d.setDate(d.getDate() + 2);
    const p = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  });
  await dialog.getByLabel("Fecha del pago").fill(tomorrow);
  await expect(dialog.getByText("La fecha de pago no puede ser futura.")).toBeVisible();
  await expect(confirm(page)).toBeDisabled();
  await shot(page, "12_fecha_futura_cliente");

  // The server is the final validation: what the UI refuses to send, the API also refuses.
  const { token } = await apiLogin(request, OPER);
  const h = { headers: bearer(token) };
  const fut = await request.post(`${API}/api/pagos`, { ...h, data: { placa: plate, fecha_pago: tomorrow, corte_esperado: null } });
  expect(fut.status()).toBe(422);
  const extra = await request.post(`${API}/api/pagos`, { ...h, data: { placa: plate, fecha_pago: isoDaysAgo(0), corte_esperado: null, valor: 1 } });
  expect(extra.status()).toBe(422);
  const noKey = await request.post(`${API}/api/pagos`, { ...h, data: { placa: plate, fecha_pago: isoDaysAgo(0) } });
  expect(noKey.status()).toBe(422);
  expect((await request.get(`${API}/api/mensualidades/${plate}?fecha_pago=${tomorrow}`, h)).status()).toBe(422);
  // Nothing was written by the rejected calls.
  expect((await apiGet(request, `/api/vehiculos/${plate}/pagos`)).body.cantidad).toBe(0);

  // Back to today: the dialog recovers.
  await dialog.getByLabel("Fecha del pago").fill(isoDaysAgo(0));
  await expect(confirm(page)).toBeEnabled();
});

test("R-07 historial: con pagos (reciente primero, nombre), vacío y semilla CAL030", async ({ page, request }) => {
  const plate = await createVehicle(request);
  const { token } = await apiLogin(request, OPER);
  const firstPay = await request.post(`${API}/api/pagos`, {
    headers: bearer(token),
    data: { placa: plate, fecha_pago: isoDaysAgo(0), corte_esperado: null },
  });
  expect(firstPay.status()).toBe(201);
  const m = await apiGet(request, `/api/mensualidades/${plate}`);
  expect(
    (await request.post(`${API}/api/pagos`, {
      headers: bearer(token),
      data: { placa: plate, fecha_pago: isoDaysAgo(0), corte_esperado: m.body.proximo_pago.corte_esperado },
    })).status(),
  ).toBe(201);

  await login(page, OPER);
  await consult(page, plate);
  await page.getByRole("button", { name: "Ver historial de pagos" }).click();
  const table = page.getByTestId("history-table");
  await expect(table.locator("tbody tr")).toHaveCount(2);
  await expect(table).not.toContainText("[object Object]");
  await expect(table.locator("tbody tr").first()).toContainText("$250.000");
  await expect(table.locator("tbody tr").first()).toContainText("Operador");
  await expect(table.locator("button, a, input")).toHaveCount(0);
  const rows = await table.locator("tbody tr").allTextContents();
  const periods = rows.map((r) => r.match(/(\d{2}\/\d{2}\/\d{4}) – (\d{2}\/\d{2}\/\d{4})/)!);
  expect(periods[0][1]).toBe(periods[1][2]); // newest first
  await expect(page.getByTestId("history-footer")).toContainText("Mostrando 2 de 2 pagos");
  await shot(page, "13_historial_con_pagos");

  const empty = await createVehicle(request);
  await consult(page, empty);
  await page.getByRole("button", { name: "Ver historial de pagos" }).click();
  await expect(page.getByTestId("history-empty")).toHaveText("Sin pagos registrados.");
  await shot(page, "14_historial_vacio");

  await consult(page, "CAL030");
  await page.getByRole("button", { name: "Ver historial de pagos" }).click();
  const srv = await apiGet(request, "/api/vehiculos/CAL030/pagos");
  await expect(page.getByTestId("history-table").locator("tbody tr")).toHaveCount(srv.body.cantidad);
  await expect(page.getByTestId("history-footer")).toContainText(`Mostrando ${srv.body.cantidad} de ${srv.body.cantidad} pagos`);
});

test("R-08 entrada: rechazada sin primer pago y por vencida, luego permitida tras pagar; salida", async ({ page, request }) => {
  const plate = await createVehicle(request);
  await login(page, OPER);
  const check = async (p: string) => {
    await page.goto("/entrada");
    await page.getByLabel("Placa").fill(p);
    await page.getByRole("button", { name: "Consultar vehículo" }).click();
  };

  // SIN_PRIMER_PAGO (created plate) and the seed twin XYZ987.
  await check(plate);
  const srv = await apiGet(request, `/api/vehiculos/${plate}/validar-ingreso`);
  expect(srv.body.codigo_motivo).toBe("SIN_PRIMER_PAGO");
  await expect(page.getByRole("alert").filter({ hasText: srv.body.motivo })).toBeVisible(); // server text, shown as is
  await expect(page.getByText("Tarifa mensual")).toBeVisible();
  await expect(page.getByRole("button", { name: /^[CM]\d\d$/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Registrar entrada" })).toHaveCount(0);
  await shot(page, "15_entrada_sin_primer_pago");
  await check("XYZ987");
  await expect(page.getByRole("link", { name: "Registrar primer pago" })).toBeVisible();

  // MENSUALIDAD_VENCIDA (JKL321, seed): renewal link, no cells.
  await check("JKL321");
  await expect(page.getByRole("link", { name: "Registrar pago de renovación" })).toBeVisible();
  await expect(page.getByRole("button", { name: /^[CM]\d\d$/ })).toHaveCount(0);
  await shot(page, "16_entrada_vencida");

  // First payment from the link, then the entry is allowed.
  await check(plate);
  await page.getByRole("link", { name: "Registrar primer pago" }).click();
  await expect(page).toHaveURL(new RegExp(`/pagos\\?placa=${plate}`));
  await expect(page.getByRole("heading", { name: `Vehículo ${plate}` })).toBeVisible();
  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  await confirm(page).click();
  await expect(page.getByTestId("payment-result")).toContainText("Estado ACTIVA");

  await check(plate);
  const cell = page.getByRole("button", { name: /^C\d\d$/ }).first();
  await expect(cell).toBeVisible();
  await cell.click();
  await page.getByRole("button", { name: "Registrar entrada" }).click();
  await expect(page.getByRole("status")).toContainText("Entrada registrada.");
  await shot(page, "17_entrada_permitida");

  // The exit is never blocked by the monthly fee (RN-36): done through the API to leave the cell free.
  const { token } = await apiLogin(request, OPER);
  const out = await request.post(`${API}/api/salidas`, { headers: bearer(token), data: { placa: plate } });
  expect(out.status()).toBe(200);
});

test("R-09 registro de vehículo nuevo (moto) → queda INACTIVA → Registrar primer pago", async ({ page, request }) => {
  const { plate, doc } = unique("RM");
  await login(page, OPER);
  await page.goto(`/registro?placa=${plate}`);
  await page.getByLabel("Documento").fill(doc);
  await page.getByLabel("Nombre completo").fill("Cliente Registro F06");
  await page.getByLabel("Tipo de vehículo").selectOption("MOTO");
  await page.getByLabel("Marca").fill("Honda");
  await page.getByLabel("Color").fill("Negro");
  await page.getByRole("button", { name: "Registrar cliente y vehículo" }).click();
  await expect(page.getByRole("status")).toContainText("INACTIVA hasta registrar el primer pago");
  await shot(page, "18_registro_nuevo");

  await page.getByRole("link", { name: "Registrar primer pago" }).click();
  await expect(page).toHaveURL(new RegExp(`/pagos\\?placa=${plate}`));
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA");
  await expect(page.getByTestId("monthly-card")).toContainText("$100.000"); // moto fee, from the server
  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  await expect(page.getByRole("dialog").getByLabel("Valor")).toHaveValue("$100.000");
  await confirm(page).click();
  await expect(page.getByTestId("payment-result")).toContainText("$100.000");
  expect((await apiGet(request, `/api/mensualidades/${plate}`)).body.estado_mensualidad).toBe("ACTIVA");
  await shot(page, "19_registro_primer_pago_moto");
});

test("R-10 /clientes: sin selector de mensualidad, etiqueta calculada y PUT sin estado", async ({ page, request }) => {
  const plate = await createVehicle(request);
  await login(page, ADMIN);
  await page.goto("/clientes");
  await page.getByLabel("Placa").fill(plate);
  await page.getByRole("button", { name: "Consultar" }).click();
  const form = page.getByRole("form", { name: `Vehículo ${plate}` });
  await expect(form.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA (calculada)");
  await expect(form.locator("select")).toHaveCount(1); // only "Tipo de vehículo"
  await form.getByLabel("Color").fill("Verde");
  await form.getByRole("button", { name: "Guardar vehículo" }).click();
  await expect(page.getByRole("status")).toContainText(/actualizado/i);
  await shot(page, "20_clientes_sin_selector");
  expect((await apiGet(request, `/api/mensualidades/${plate}`)).body.vehiculo.color).toBe("Verde");
});

test("R-11 COR001 (corte hoy) y CAL031 (día 31): lo que muestra la pantalla coincide con el servidor", async ({ page, request }) => {
  await login(page, OPER);
  const cor = await apiGet(request, "/api/mensualidades/COR001");
  await consult(page, "COR001");
  await expect(page.getByTestId("monthly-state")).toHaveText(`Mensualidad ${cor.body.estado_mensualidad}`);
  await expect(page.getByTestId("monthly-card")).toContainText(`Fecha de corte (vencimiento)${dmy(cor.body.fecha_corte)}`);
  expect(cor.body.fecha_corte).toBe(cor.body.proximo_pago.fecha_pago); // corte == hoy del servidor
  expect(cor.body.estado_mensualidad).toBe("INACTIVA"); // the cut-off day is already inactive
  await shot(page, "21_cor001");
  await page.goto("/entrada");
  await page.getByLabel("Placa").fill("COR001");
  await page.getByRole("button", { name: "Consultar vehículo" }).click();
  await expect(page.getByRole("link", { name: "Registrar pago de renovación" })).toBeVisible();

  const cal = await apiGet(request, "/api/mensualidades/CAL031");
  await consult(page, "CAL031");
  await expect(page.getByTestId("monthly-card")).toContainText(`Fecha de inicio${dmy(cal.body.fecha_inicio)}`);
  await expect(page.getByTestId("monthly-card")).toContainText(`Día de corte${cal.body.dia_corte}`);
  await expect(page.getByTestId("monthly-card")).toContainText(`Fecha de corte (vencimiento)${dmy(cal.body.fecha_corte)}`);
  await page.getByRole("button", { name: "Renovar mensualidad" }).click();
  await expect(page.getByTestId("cutoff-day")).toHaveText("31");
  await expect(page.getByTestId("next-cutoff")).toHaveText(dmy(cal.body.proximo_pago.periodo_fin)); // no clamping done by the UI
  await shot(page, "22_cal031_renovacion");
});

test("R-12 404 de placa inexistente y 401 tras revocar la sesión", async ({ page, request }) => {
  await login(page, OPER);
  await consult(page, "XYZ987"); // sanity: session works
  await page.getByLabel("Placa").fill("ZZZ000");
  await page.getByRole("button", { name: "Consultar", exact: true }).click();
  const nf = await apiGet(request, "/api/mensualidades/ZZZ000");
  expect(nf.status).toBe(404);
  await expect(page.getByRole("alert").filter({ hasText: nf.body.mensaje })).toBeVisible();
  await expect(page.getByTestId("monthly-card")).toHaveCount(0);
  await shot(page, "23_placa_inexistente");

  // Revoke this tab's session from outside: the next call answers 401 and the app goes to /login.
  const token = await page.evaluate(() => sessionStorage.getItem("ac.token"));
  expect((await request.post(`${API}/api/auth/logout`, { headers: bearer(token!) })).status()).toBe(200);
  await page.getByLabel("Placa").fill("XYZ987");
  await page.getByRole("button", { name: "Consultar", exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
});

