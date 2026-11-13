import { defineConfig } from "@playwright/test";

// E2E_MODE=mock (default): starts Next with the in-memory fake API  -> results are [mock].
// E2E_MODE=real: expects the real backend (NEXT_PUBLIC_API_URL) and a frontend
// already built against it on E2E_BASE_URL                           -> results are [real].
const mode = process.env.E2E_MODE ?? "mock";
const port = 3100;

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  workers: 1,
  fullyParallel: false,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? `http://127.0.0.1:${port}`,
    viewport: { width: 1440, height: 900 },
    locale: "es-CO",
  },
  webServer:
    mode === "mock"
      ? {
          command: `npx next build && npx next start -p ${port}`,
          url: `http://127.0.0.1:${port}/login`,
          env: { NEXT_PUBLIC_USE_MOCK: "true" },
          reuseExistingServer: false,
          timeout: 120_000,
        }
      : undefined,
});
