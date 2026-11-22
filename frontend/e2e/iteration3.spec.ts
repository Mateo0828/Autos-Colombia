import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

// Iteration 3 (payments) against the in-memory mock: every result is [mock].
// F-06: the mock now answers with the shapes and plates of the real backend (D-39).
// The flags below only exist in the mock (src/lib/mock.ts), so the suite is skipped in real mode.
const MODE = process.env.E2E_MODE ?? "mock";
test.skip(MODE !== "mock", "usa el mock y sus banderas de prueba");

const SHOTS =
  process.env.CAPTURES_DIR ??
  path.resolve(__dirname, "../../../CLAUDE_FILES/AutosColombia_intercambio/informes/capturas");

const ADMIN = { user: "admin", pass: "Admin12345" };
const OPER = { user: "operador1", pass: "Operador123" };

const shot = (page: Page, name: string) =>
  page.screenshot({ path: path.join(SHOTS, `f06_mock_${name}.png`), fullPage: true });

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
  // Retry the fill: a hydration that lands right after it can wipe the value.
  await expect(async () => {
    await page.getByLabel("Placa").fill(plate);
    await expect(button).toBeEnabled({ timeout: 500 });
  }).toPass({ timeout: 10_000 });
  await button.click();
}

/** Next mock payment answers as the flag says (see header of mock.ts). */
const setFlags = (page: Page, flags: Record<string, boolean>) =>
  page.evaluate((f) => sessionStorage.setItem("ac.mock.flags", JSON.stringify(f)), flags);

/** AAAA-MM-DD of the browser's day shifted by `days` (only to build inputs for the date field). */
const isoDaysFromToday = (page: Page, days: number) =>
  page.evaluate((n) => {
    const d = new Date();
    d.setDate(d.getDate() + n);
    const p = (x: number) => String(x).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }, days);

/** dd/mm/aaaa of the browser's today, only to state what the test expects to see. */
const todayDisplay = (page: Page) =>
  page.evaluate(() => {
    const d = new Date();
    const p = (n: number) => String(n).padStart(2, "0");
    return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}`;
  });

test("M-01 primer pago (operador): tarjeta, ventana con día de corte y estado resultante; moto con tarifa $100.000", async ({ page }) => {
  await login(page, OPER);
  await expect(page.getByRole("link", { name: "Pagos" })).toBeVisible();
  await page.getByRole("link", { name: "Pagos" }).click();
  // Wait for the navigation: /entrada also has a "Placa" field and would take the fill.
  await expect(page).toHaveURL(/\/pagos$/);
  await expect(page.getByRole("heading", { name: "Consultar mensualidad" })).toBeVisible();

  await page.getByLabel("Placa").fill("mot02a");
  await page.getByRole("button", { name: "Consultar", exact: true }).click();
  await expect(page.getByTestId("monthly-card")).toContainText("$100.000");
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA");

  await consult(page, "XYZ987");
  const card = page.getByTestId("monthly-card");
  await expect(card).toContainText("$250.000");
  await expect(card).toContainText("Pagos registrados0");
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA");
  await shot(page, "01_primer_pago_tarjeta");

  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByLabel("Valor")).toHaveValue("$250.000");
  await expect(dialog.getByLabel("Valor")).toHaveAttribute("readonly", "");
  await expect(page.getByTestId("resulting-state")).toHaveText("ACTIVA");
  await expect(page.getByTestId("cutoff-day")).toContainText("primer pago"); // first payment: not defined yet
  await expect(page.getByTestId("advance-notice")).toHaveCount(0); // not advance: no payments yet
  const next = (await page.getByTestId("next-cutoff").textContent())!;
  expect(next).toMatch(/^\d{2}\/\d{2}\/\d{4}$/);
  await shot(page, "02_primer_pago_ventana");
  await dialog.getByRole("button", { name: "Confirmar pago" }).click();

  const result = page.getByTestId("payment-result");
  await expect(result).toContainText("Pago registrado correctamente.");
  await expect(result).toContainText("$250.000");
  await expect(result).toContainText(`Nueva fecha de corte ${next}`);
  await expect(result).toContainText("Estado ACTIVA");
  await expect(result).toContainText("Registrado por Operador Mañana"); // registrado_por.nombre, not an object dump
  await expect(page.getByTestId("payment-warning")).toHaveCount(0);
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad ACTIVA");
  await expect(card).toContainText("Pagos registrados1");
  await expect(card).toContainText(/Día de corte\d+/); // dia_corte shown once there is a payment
  await shot(page, "03_primer_pago_resultado");
});

test("M-02 renovación anticipada (administrador): aviso «Pago anticipado» y corte del servidor", async ({ page }) => {
  await login(page, ADMIN);
  await consult(page, "ABC123");
  const card = page.getByTestId("monthly-card");
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad ACTIVA");
  await expect(card).toContainText("Pagos registrados1");
  await page.getByRole("button", { name: "Renovar mensualidad" }).click();
  await expect(page.getByTestId("advance-notice")).toContainText("Pago anticipado");
  await expect(page.getByTestId("resulting-state")).toHaveText("ACTIVA");
  const next = (await page.getByTestId("next-cutoff").textContent())!;
  await shot(page, "04_renovacion_anticipada_ventana");
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar pago" }).click();

  await expect(page.getByTestId("payment-result")).toContainText(`Nueva fecha de corte ${next}`);
  await expect(page.getByTestId("payment-warning")).toHaveCount(0);
  await expect(card).toContainText("Pagos registrados2");
  await expect(card).toContainText(`Fecha de corte (vencimiento)${next}`);
  await shot(page, "05_renovacion_anticipada_resultado");
});

test("M-03 renovación tardía de JKL321: se recupera (ACTIVA, sin advertencia) y el período arranca en el corte anterior", async ({ page }) => {
  await login(page, OPER);
  await consult(page, "JKL321");
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA");
  const card = page.getByTestId("monthly-card");
  const corteAnterior = (await card.textContent())!.match(/vencimiento\)(\d{2}\/\d{2}\/\d{4})/)![1];
  await page.getByRole("button", { name: "Renovar mensualidad" }).click();
  await expect(page.getByTestId("advance-notice")).toHaveCount(0);
  await expect(page.getByTestId("resulting-state")).toHaveText("ACTIVA");
  await expect(page.getByTestId("projection-warning")).toHaveCount(0);
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar pago" }).click();
  const result = page.getByTestId("payment-result");
  await expect(result).toContainText(`Período ${corteAnterior} al `); // RN-26: starts at the previous cut-off
  await expect(result).toContainText("Estado ACTIVA");
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad ACTIVA");
  await shot(page, "06_renovacion_tardia_recupera");
});

test("M-03b pago histórico: al cambiar la fecha se vuelve a consultar y aparece la advertencia (queda INACTIVA)", async ({ page }) => {
  await login(page, OPER);
  await consult(page, "XYZ987");
  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  const dialog = page.getByRole("dialog");
  await expect(page.getByTestId("resulting-state")).toHaveText("ACTIVA");
  await expect(page.getByTestId("projection-warning")).toHaveCount(0);
  // A payment dated ~70 days ago: the server projects INACTIVA with a warning for THAT date.
  const old = await isoDaysFromToday(page, -70);
  await dialog.getByLabel("Fecha del pago").fill(old);
  await expect(page.getByTestId("resulting-state")).toHaveText("INACTIVA");
  await expect(page.getByTestId("projection-warning")).toContainText("no cubre la fecha actual");
  await expect(page.getByTestId("next-cutoff")).not.toHaveText("—");
  await shot(page, "06b_pago_historico_ventana");
  await dialog.getByRole("button", { name: "Confirmar pago" }).click();
  await expect(page.getByTestId("payment-result")).toContainText("Estado INACTIVA");
  await expect(page.getByTestId("payment-warning")).toContainText("no cubre la fecha actual");
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA");
  await shot(page, "06c_pago_historico_resultado");
});

test("M-04 409: mensaje del servidor y recarga automática de la consulta", async ({ page }) => {
  await login(page, OPER);
  await consult(page, "ABC123");
  await expect(page.getByTestId("monthly-card")).toContainText("Pagos registrados1");
  // Another operator pays first: this payment's corte_esperado no longer matches.
  await setFlags(page, { concurrent: true });
  await page.getByRole("button", { name: "Renovar mensualidad" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar pago" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "La mensualidad ya fue actualizada; consulte de nuevo." })).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByTestId("monthly-card")).toContainText("Pagos registrados2"); // reloaded
  await expect(page.getByTestId("payment-result")).toHaveCount(0);
  await shot(page, "07_conflicto_409");

  // Forced 409 without state change: same message, no result shown.
  await setFlags(page, { force409: true });
  await page.getByRole("button", { name: "Renovar mensualidad" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar pago" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "ya fue actualizada" })).toBeVisible();
  await expect(page.getByTestId("monthly-card")).toContainText("Pagos registrados2");
});

test("M-05 422: error en la ventana y reintento; fecha futura bloqueada en el cliente", async ({ page }) => {
  await login(page, OPER);
  await consult(page, "XYZ987");
  await setFlags(page, { force422: true });
  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: "Confirmar pago" }).click();
  await expect(dialog.getByRole("alert")).toContainText("La fecha de pago no es válida.");
  await shot(page, "08_pago_422");

  // Future date: rejected by the client without calling the API.
  const tomorrow = await page.evaluate(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    const p = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  });
  await dialog.getByLabel("Fecha del pago").fill(tomorrow);
  await expect(dialog.getByText("La fecha de pago no puede ser futura.")).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Confirmar pago" })).toBeDisabled();

  // Retry with today (flag already consumed) succeeds.
  await dialog.getByLabel("Fecha del pago").fill(await page.evaluate(() => {
    const d = new Date();
    const p = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }));
  await dialog.getByRole("button", { name: "Confirmar pago" }).click();
  await expect(page.getByTestId("payment-result")).toContainText("Pago registrado correctamente.");
});

test("M-06 historial: con pagos (más reciente primero, registrado_por.nombre, solo lectura) y sin pagos", async ({ page }) => {
  await login(page, OPER);
  await consult(page, "CAL030"); // 20+ payments, as in the real seed
  await page.getByRole("button", { name: "Ver historial de pagos" }).click();
  const table = page.getByTestId("history-table");
  await expect(table).toBeVisible();
  expect(await table.locator("tbody tr").count()).toBeGreaterThan(20);
  await expect(table.locator("tbody tr").first()).toContainText("$250.000");
  await expect(table.locator("tbody tr").first()).toContainText("Operador Mañana"); // a name, not [object Object]
  await expect(table).not.toContainText("[object Object]");
  await expect(table.locator("button, a, input")).toHaveCount(0); // no edit/delete
  // Newest first: the first row's period starts where the second row's ends.
  const rows = await table.locator("tbody tr").allTextContents();
  const periods = rows.slice(0, 2).map((r) => r.match(/(\d{2}\/\d{2}\/\d{4}) – (\d{2}\/\d{2}\/\d{4})/)!);
  expect(periods[0][1]).toBe(periods[1][2]);
  await expect(page.getByTestId("history-footer")).toContainText(/Mostrando (\d+) de \1 pagos · ordenados del más reciente al más antiguo/);
  await shot(page, "09_historial_con_pagos");

  await consult(page, "XYZ987");
  await page.getByRole("button", { name: "Ver historial de pagos" }).click();
  await expect(page.getByTestId("history-empty")).toHaveText("Sin pagos registrados.");
  await shot(page, "10_historial_vacio");
});

test("M-07 entrada rechazada por mensualidad → Registrar pago → entrada permitida", async ({ page }) => {
  await login(page, OPER);
  await page.goto("/entrada");
  await page.getByLabel("Placa").fill("XYZ987");
  await page.getByRole("button", { name: "Consultar vehículo" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "no tiene un primer pago" })).toBeVisible();
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA");
  await expect(page.getByText("Tarifa mensual")).toBeVisible(); // m12: monthly data shown with the block
  await expect(page.getByRole("button", { name: /^C\d\d$/ })).toHaveCount(0); // no cells offered
  await expect(page.getByRole("button", { name: "Registrar entrada" })).toHaveCount(0);
  await shot(page, "11_entrada_rechazada_mensualidad");

  await page.getByRole("link", { name: "Registrar primer pago" }).click();
  await expect(page).toHaveURL(/\/pagos\?placa=XYZ987/);
  await expect(page.getByRole("heading", { name: "Vehículo XYZ987" })).toBeVisible(); // consulted automatically
  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar pago" }).click();
  await expect(page.getByTestId("payment-result")).toContainText("Estado ACTIVA");

  await page.goto("/entrada");
  await page.getByLabel("Placa").fill("XYZ987");
  await page.getByRole("button", { name: "Consultar vehículo" }).click();
  await page.getByRole("button", { name: "C02", exact: true }).click();
  await page.getByRole("button", { name: "Registrar entrada" }).click();
  await expect(page.getByRole("status")).toContainText("Entrada registrada. Celda C02 ocupada");
  await shot(page, "12_entrada_tras_pago");

  // Exit never depends on the monthly fee (RN-36): not touched, still reachable.
  await page.goto("/salida?placa=XYZ987");
  await expect(page.getByTestId("operator-label")).toBeVisible();
});

test("M-08 registro de vehículo nuevo → queda INACTIVA → Registrar primer pago", async ({ page }) => {
  await login(page, OPER);
  await page.goto("/registro?placa=NEW123");
  await page.getByLabel("Documento").fill("9000111222");
  await page.getByLabel("Nombre completo").fill("Cliente Nuevo");
  await page.getByLabel("Tipo de vehículo").selectOption("MOTO");
  await page.getByLabel("Marca").fill("Honda");
  await page.getByLabel("Color").fill("Rojo");
  await page.getByRole("button", { name: "Registrar cliente y vehículo" }).click();
  await expect(page.getByRole("status")).toContainText("INACTIVA hasta registrar el primer pago");
  await expect(page.getByText("Ir a registrar la entrada")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Volver a Entrada" })).toBeVisible();
  await shot(page, "13_registro_inactiva");

  await page.getByRole("link", { name: "Registrar primer pago" }).click();
  await expect(page).toHaveURL(/\/pagos\?placa=NEW123/);
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA");
  await expect(page.getByTestId("monthly-card")).toContainText("$100.000");
  await expect(page.getByTestId("monthly-card")).toContainText("Pagos registrados0");
  await expect(page.getByRole("button", { name: "Registrar primer pago" })).toBeVisible();
  await shot(page, "14_registro_a_primer_pago");
});

test("M-09 /clientes: sin selector de mensualidad, etiqueta de solo lectura y PUT sin estado", async ({ page }) => {
  await login(page, ADMIN);
  await page.goto("/clientes");
  await page.getByLabel("Placa").fill("ABC123");
  await page.getByRole("button", { name: "Consultar" }).click();
  const form = page.getByRole("form", { name: "Vehículo ABC123" });
  await expect(form.getByTestId("monthly-state")).toHaveText("Mensualidad ACTIVA (calculada)");
  await expect(form.locator("select")).toHaveCount(1); // only "Tipo de vehículo"
  await form.getByLabel("Color").fill("Verde");
  await form.getByRole("button", { name: "Guardar vehículo" }).click();
  // The mock answers 422 if the PUT carried estado_mensualidad, so a success proves it was not sent.
  await expect(page.getByRole("status")).toContainText(/actualizado/i);
  await shot(page, "15_clientes_sin_selector");
});

test("M-10 casos de fechas: COR001 (corte hoy) y CAL031 (día 31 de origen)", async ({ page }) => {
  await login(page, OPER);
  await consult(page, "COR001");
  const today = await todayDisplay(page);
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad INACTIVA"); // the cut-off day is already inactive
  await expect(page.getByTestId("monthly-card")).toContainText(`Fecha de corte (vencimiento)${today}`);
  await shot(page, "16_corte_hoy");
  await page.goto("/entrada");
  await page.getByLabel("Placa").fill("COR001");
  await page.getByRole("button", { name: "Consultar vehículo" }).click();
  await expect(page.getByRole("link", { name: "Registrar pago de renovación" })).toBeVisible(); // MENSUALIDAD_VENCIDA

  await consult(page, "CAL031");
  await expect(page.getByTestId("monthly-card")).toContainText("Fecha de inicio31/01/2025");
  await expect(page.getByTestId("monthly-card")).toContainText("Día de corte31");
  await expect(page.getByTestId("monthly-state")).toHaveText("Mensualidad ACTIVA");
  await page.getByRole("button", { name: "Renovar mensualidad" }).click();
  await expect(page.getByTestId("cutoff-day")).toHaveText("31");
  await shot(page, "17_primer_pago_dia_31");
});

test("M-12 el «hoy» del servidor (proximo_pago.fecha_pago de la primera consulta) manda sobre el reloj del navegador", async ({ page }) => {
  await login(page, OPER);
  // The server says today is another day than the browser: the dialog must follow the server.
  await page.evaluate(() => sessionStorage.setItem("ac.mock.fakeHoy", "2026-01-15"));
  await consult(page, "XYZ987");
  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  await expect(page.getByLabel("Fecha del pago")).toHaveValue("2026-01-15");
  await expect(page.getByLabel("Fecha del pago")).toHaveAttribute("max", "2026-01-15");
});

test("M-13 corte_esperado (D-36): el cuerpo lleva null en el primer pago y la fecha de corte en renovaciones, sin `valor`", async ({ page }) => {
  await login(page, OPER);
  const bodies: Record<string, unknown>[] = [];
  // The mock lives in the page, so record what the UI passes to fetch-less api: wrap JSON.stringify of payment bodies.
  await page.addInitScript(() => {
    const orig = JSON.stringify;
    (window as unknown as { __pay: unknown[] }).__pay = [];
    JSON.stringify = function (v: unknown, ...rest: never[]) {
      if (v && typeof v === "object" && "corte_esperado" in (v as object))
        (window as unknown as { __pay: unknown[] }).__pay.push(v);
      return (orig as (...a: unknown[]) => string)(v, ...rest);
    } as typeof JSON.stringify;
  });
  await consult(page, "XYZ987");
  await page.getByRole("button", { name: "Registrar primer pago" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar pago" }).click();
  await expect(page.getByTestId("payment-result")).toBeVisible();
  await page.getByRole("button", { name: "Renovar mensualidad" }).click();
  const cutoff = (await page.getByTestId("monthly-card").textContent())!.match(/(\d{2}\/\d{2}\/\d{4})Día de corte/)![1];
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar pago" }).click();
  await expect(page.getByTestId("monthly-card")).toContainText("Pagos registrados2");
  bodies.push(...(await page.evaluate(() => (window as unknown as { __pay: Record<string, unknown>[] }).__pay)));
  expect(bodies).toHaveLength(2);
  expect(bodies[0]).toMatchObject({ placa: "XYZ987", corte_esperado: null });
  expect(bodies[1].corte_esperado).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  expect(bodies[1].corte_esperado).toBe(cutoff.split("/").reverse().join("-"));
  for (const b of bodies) expect(Object.keys(b).sort()).toEqual(["corte_esperado", "fecha_pago", "placa"]);
});

test("M-11 placa inexistente (404), placa inválida y acceso sin sesión", async ({ page }) => {
  await login(page, OPER);
  await consult(page, "ZZZ000");
  await expect(page.getByRole("alert").filter({ hasText: "El vehículo no se encuentra registrado." })).toBeVisible();
  await expect(page.getByTestId("monthly-card")).toHaveCount(0);
  await shot(page, "18_placa_inexistente");
  await page.getByLabel("Placa").fill("AB-12");
  await page.getByRole("button", { name: "Consultar", exact: true }).click();
  await expect(page.getByText("La placa solo puede contener letras y números (máximo 10).")).toBeVisible();

  await page.getByRole("button", { name: "Cerrar sesión" }).first().click();
  await expect(page).toHaveURL(/\/login/);
  await page.goto("/pagos");
  await expect(page).toHaveURL(/\/login/);
});
