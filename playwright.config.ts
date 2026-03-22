import { defineConfig, devices } from '@playwright/test';

const isCI = Boolean(process.env.CI);

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
    baseURL: 'http://localhost:3000',
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
  webServer: [
    {
      command: 'python3 qa/scripts/run_seeded_api.py',
      url: 'http://localhost:8000/health',
      reuseExistingServer: !isCI,
      timeout: 120_000,
    },
    {
      command: 'cd apps/web && pnpm exec next dev -p 3000 --hostname localhost',
      url: 'http://localhost:3000',
      reuseExistingServer: !isCI,
      timeout: 120_000,
      env: {
        ...process.env,
        NEXT_PUBLIC_APP_URL: 'http://localhost:3000',
        NEXT_PUBLIC_API_URL: 'http://localhost:8000',
        INTERNAL_API_URL: 'http://localhost:8000',
        SESSION_COOKIE_SECURE: 'false',
        SESSION_COOKIE_DOMAIN: '',
        NEXT_PUBLIC_GA_MEASUREMENT_ID: '',
        NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION: '',
      },
    },
  ],
});
