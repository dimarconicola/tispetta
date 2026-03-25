import { defineConfig, devices } from '@playwright/test';

const isCI = Boolean(process.env.CI);
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3100';
const skipWebServer = process.env.PLAYWRIGHT_SKIP_WEBSERVER === '1';

export default defineConfig({
  testDir: './apps/web/tests/e2e',
  timeout: 45_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  workers: 1,
  reporter: isCI ? [['github'], ['html', { open: 'never' }]] : [['list']],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'critical-chromium',
      use: {
        ...devices['Desktop Chrome'],
      },
    },
  ],
  webServer: skipWebServer
    ? undefined
    : [
        {
          command: 'python3 qa/scripts/run_seeded_api.py',
          url: 'http://localhost:8100/health',
          reuseExistingServer: false,
          timeout: 120_000,
          env: {
            ...process.env,
            PLAYWRIGHT_APP_BASE_URL: 'http://localhost:3100',
            PLAYWRIGHT_API_PORT: '8100',
          },
        },
        {
          command: 'cd apps/web && pnpm exec next dev -p 3100 --hostname localhost',
          url: 'http://localhost:3100',
          reuseExistingServer: false,
          timeout: 120_000,
          env: {
            ...process.env,
            NEXT_PUBLIC_APP_URL: 'http://localhost:3100',
            NEXT_PUBLIC_API_URL: 'http://localhost:8100',
            INTERNAL_API_URL: 'http://localhost:8100',
            SESSION_COOKIE_SECURE: 'false',
            SESSION_COOKIE_DOMAIN: '',
            NEXT_PUBLIC_GA_MEASUREMENT_ID: '',
            NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION: '',
          },
        },
      ],
});
