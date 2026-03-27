import type { Route } from 'next';

export type OnboardingStepKey =
  | 'personal_core'
  | 'business_context'
  | 'business_core'
  | 'results_checkpoint'
  | 'strategic_modules'
  | 'final_next_actions';

const OPTION_LABELS_IT: Record<string, string> = {
  not_started: 'Idea o attivita non ancora aperta',
  partita_iva_only: 'Partita IVA o attivita individuale',
  incorporated_business: 'Societa gia costituita',
  individual_professional: 'Libero professionista',
  sole_proprietorship: 'Ditta individuale',
  srl: 'SRL',
  innovative_startup: 'Startup innovativa',
  startup_innovativa: 'Startup innovativa',
  pmi_innovativa: 'PMI innovativa',
  cooperative: 'Cooperativa',
  other: 'Altra forma',
  not_sure: 'Non lo so ancora',
  idea: 'Solo idea o progetto',
  '0-12m': 'Meno di 12 mesi',
  '1-3y': 'Da 1 a 3 anni',
  '3-5y': 'Da 3 a 5 anni',
  '5y+': 'Oltre 5 anni',
  solo: 'Solo founder',
  micro: 'Micro',
  small: 'Piccola',
  medium: 'Media',
  none: 'Nessuno',
  retail: 'Commercio',
  creative: 'Creativo',
  dipendente: 'Dipendente',
  autonomo: 'Autonomo o freelance',
  disoccupato: 'Disoccupato',
  pensionato: 'Pensionato',
  under_35: 'Under 35',
  '35_55': 'Tra 35 e 55 anni',
  over_55: 'Over 55',
  single: 'Single',
  coppia_senza_figli: 'Coppia senza figli',
  coppia_con_figli: 'Coppia con figli',
  genitore_solo_con_figli: 'Genitore solo con figli',
  under_15k: 'Sotto 15.000 EUR',
  '15_25k': 'Tra 15.000 e 25.000 EUR',
  '25_40k': 'Tra 25.000 e 40.000 EUR',
  over_40k: 'Oltre 40.000 EUR',
  non_determinato: 'Non determinato',
  '3_plus': '3 o piu',
  persona_fisica: 'Solo profilo personale',
  digitale: 'Digitale',
  manifattura: 'Manifattura',
  servizi: 'Servizi',
  turismo: 'Turismo',
  energia: 'Energia',
  agritech: 'Agritech',
  true: 'Si',
  false: 'No',
};

export function formatOptionLabel(option: string): string {
  return OPTION_LABELS_IT[option] ?? option.replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export function buildOnboardingHref(
  step: OnboardingStepKey,
  module?: string,
  entry?: string,
  returnTo?: string,
): Route {
  const search = new URLSearchParams();
  search.set('step', step);
  if (module) search.set('module', module);
  if (entry) search.set('entry', entry);
  if (returnTo) search.set('return_to', returnTo);
  return (`/onboarding?${search.toString()}`) as Route;
}

export function buildProfileEditHref(
  target: { step: string; module: string | null } | null | undefined,
  options?: { entry?: string; returnTo?: string },
): Route {
  const step = (target?.step ?? 'personal_core') as OnboardingStepKey;
  return buildOnboardingHref(step, target?.module ?? undefined, options?.entry, options?.returnTo);
}
