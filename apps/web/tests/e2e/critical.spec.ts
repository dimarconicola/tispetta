import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

const API_BASE_URL = process.env.PLAYWRIGHT_API_URL ?? 'http://localhost:8000';

function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

async function loginViaApi(page: Page, request: APIRequestContext, email: string, redirectTo = '/search') {
  const response = await request.post(`${API_BASE_URL}/v1/auth/request-magic-link`, {
    data: { email, redirect_to: redirectTo },
  });
  expect(response.ok()).toBeTruthy();

  const payload = (await response.json()) as { preview_url: string | null };
  expect(payload.preview_url).toBeTruthy();
  await page.goto(payload.preview_url as string);
}

test('start_magic_link_login_flow', async ({ page }) => {
  const email = uniqueEmail('auth-start');

  await page.goto('/start');
  await expect(page.getByText('Entra nel motore da un percorso piu corto')).toBeVisible();
  await page.getByLabel('Email').fill(email);
  await page.getByRole('button', { name: 'Invia link e continua' }).click();
  await expect(page.getByRole('link', { name: 'Apri link di anteprima' })).toBeVisible();
  await page.getByRole('link', { name: 'Apri link di anteprima' }).click();

  await expect(page).toHaveURL(/\/onboarding\?entry=apex/);
  await expect(page.getByText('Per chi stai cercando opportunita?')).toBeVisible();
});

test('impresa_onboarding_core_to_results', async ({ page, request }) => {
  const email = uniqueEmail('onboarding');
  await loginViaApi(page, request, email, '/onboarding?entry=apex');

  await expect(page.getByText('Per chi stai cercando opportunita?')).toBeVisible();
  await page.getByRole('button', { name: /Attivita o impresa/i }).click();

  await page.locator('#activity_stage').selectOption('incorporated_business');
  await page.locator('#legal_form_bucket').selectOption('srl');
  await page.locator('#main_operating_region').selectOption('Lombardia');
  await page.locator('#company_age_or_formation_window').selectOption('1-3y');
  await page.locator('#size_band').selectOption('micro');
  await page.locator('#sector_macro_category').selectOption('digitale');
  await page.locator('#innovation_regime_status').selectOption('startup_innovativa');
  await page.getByRole('button', { name: 'Salva il core e mostra i risultati' }).click();

  await expect(page).toHaveURL(/step=results/);
  await expect(page.getByText('Hai gia una prima lettura spendibile')).toBeVisible();
  await expect(page.getByText('I primi match sono gia leggibili')).toBeVisible();
});

test('persona_fisica_onboarding_core_to_results', async ({ page, request }) => {
  const email = uniqueEmail('persona');
  await loginViaApi(page, request, email, '/onboarding?entry=apex');

  await expect(page.getByText('Per chi stai cercando opportunita?')).toBeVisible();
  await page.getByRole('button', { name: /Persona fisica/i }).click();

  await expect(page.getByText('Hai scelto il percorso Persona fisica')).toBeVisible();
  await page.getByRole('button', { name: 'Salva il core e mostra i risultati' }).click();

  await expect(page).toHaveURL(/step=results/);
  await expect(page.getByText('Le risposte che sbloccano piu opportunita')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Apri il catalogo completo' })).toBeVisible();
});

test('anonymous_search_and_detail', async ({ page }) => {
  await page.goto('/search');
  await expect(page.getByText('Intelligenza delle opportunita.')).toBeVisible();
  await page.getByRole('textbox').fill('smart');
  await page.getByRole('button', { name: 'Cerca' }).click();

  await expect(page).toHaveURL(/query=smart/);
  await expect(page.getByText(/opportunita trovate/i)).toBeVisible();
  await page.getByRole('link', { name: 'Apri dettaglio' }).first().click();

  await expect(page).toHaveURL(/\/opportunities\//);
  await expect(page.getByText('Perche emerge adesso')).toBeVisible();
  await expect(page.getByText('Fonti ufficiali')).toBeVisible();
  await expect(page.locator('a[href^="https://"]').filter({ hasText: 'https://' }).first()).toBeVisible();
});

test('authenticated_save_and_saved_page', async ({ page, request }) => {
  const email = uniqueEmail('saved');
  await loginViaApi(page, request, email, '/search');

  await expect(page).toHaveURL(/\/search/);
  const firstSaveButton = page.getByRole('button', { name: 'Salva' }).first();
  await firstSaveButton.click();
  await expect(page.getByRole('button', { name: 'Salvata' }).first()).toBeVisible();

  await page.goto('/saved');
  await expect(page.getByText('La tua shortlist da monitorare.')).toBeVisible();
  await expect(page.getByRole('heading', { name: /opportunita salvate/i })).toBeVisible();
});

test('logout_clears_session', async ({ page, request }) => {
  const email = uniqueEmail('logout');
  await loginViaApi(page, request, email, '/search');

  await expect(page).toHaveURL(/\/search/);
  await page.getByRole('button', { name: 'Esci' }).click();
  await expect(page).toHaveURL(/\/auth\/sign-in/);

  await page.goto('/saved');
  await expect(page).toHaveURL(/\/auth\/sign-in/);
});
