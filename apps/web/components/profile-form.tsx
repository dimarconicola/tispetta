'use client';

import Link from 'next/link';
import { useMemo, useState, useTransition } from 'react';
import { useForm } from 'react-hook-form';

import type { Profile, ProfileQuestion } from '@/lib/types';

const API_URL = '/api/proxy';

const MODULE_COPY: Record<string, { eyebrow: string; title: string; body: string; stepLabel: string }> = {
  core_entity: {
    eyebrow: 'Step 1 di 3',
    title: 'Chiudi il perimetro stabile',
    body: 'Completa solo i fatti che spostano davvero l’ammissibilita iniziale. Dopo questo salvataggio vedi subito i primi match.',
    stepLabel: 'Core Entity',
  },
  strategic_intent: {
    eyebrow: 'Step 2 di 3',
    title: 'Aumenta la precisione sui progetti reali',
    body: 'Queste domande migliorano ranking e copertura su export, investimenti digitali, energia e hiring. Non bloccano i risultati gia visibili.',
    stepLabel: 'Strategic Intent',
  },
  conditional_accuracy: {
    eyebrow: 'Step 3 di 3',
    title: 'Chiudi solo le ambiguita residue',
    body: 'Qui compaiono solo le domande che una famiglia di misure attiva richiede davvero per chiarire lo stato.',
    stepLabel: 'Conditional Accuracy',
  },
};

type StepKey = 'core' | 'strategic' | 'conditional';

export function ProfileForm({
  profile,
  questions,
  currentStep,
  entry,
}: {
  profile: Profile | null;
  questions: ProfileQuestion[];
  currentStep: StepKey;
  entry?: string;
}) {
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [gatePassed, setGatePassed] = useState(Boolean(resolveUserType(profile)));
  const initialValues = useMemo(() => buildInitialValues(profile), [profile]);
  const { register, handleSubmit, watch, setValue } = useForm<Record<string, string | boolean | null>>({
    defaultValues: initialValues,
  });

  const userType = (watch('profile_type') as string | undefined) || resolveUserType(profile) || 'startup';
  const visibleQuestions = useMemo(
    () => questions.filter((question) => !question.audience || question.audience.includes(userType)),
    [questions, userType]
  );
  const grouped = useMemo(() => {
    const buckets: Record<string, ProfileQuestion[]> = {
      core_entity: [],
      strategic_intent: [],
      conditional_accuracy: [],
    };
    for (const question of visibleQuestions) {
      const moduleKey = question.module ?? 'core_entity';
      const bucket = buckets[moduleKey] ?? [];
      bucket.push(question);
      buckets[moduleKey] = bucket;
    }
    return buckets;
  }, [visibleQuestions]);

  const currentModule = currentStep === 'core' ? 'core_entity' : currentStep === 'strategic' ? 'strategic_intent' : 'conditional_accuracy';
  const currentQuestions = grouped[currentModule] ?? [];
  const hasConditionalQuestions = (grouped.conditional_accuracy ?? []).length > 0;
  const moduleCopy: (typeof MODULE_COPY)[keyof typeof MODULE_COPY] =
    MODULE_COPY[currentModule] ?? MODULE_COPY.core_entity!;

  return (
    <form
      className="stack"
      onSubmit={handleSubmit((values) => {
        startTransition(async () => {
          setMessage(null);
          const normalized = {
            fact_values: Object.fromEntries(
              currentQuestions
                .map((question) => [question.key, normalizeValue(question, values[question.key])])
                .filter(([, value]) => value !== undefined)
            ),
          };
          const response = await fetch(`${API_URL}/v1/profile`, {
            method: 'PUT',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(normalized),
          });
          if (!response.ok) {
            setMessage('Aggiornamento non riuscito.');
            return;
          }
          const next = nextHref(currentStep, hasConditionalQuestions, entry);
          window.location.assign(next);
        });
      })}
    >
      {!gatePassed ? (
        <div className="stack">
          <div className="panel stack">
            <p className="eyebrow">Ingresso</p>
            <h2 style={{ fontSize: '2rem' }}>Per chi stai cercando opportunita?</h2>
            <p className="subtle">Serve solo a scegliere il ramo giusto. Il resto delle domande resta nel core a massimo 8 risposte.</p>
          </div>
          <div className="grid cards-2">
            <button
              type="button"
              className="card stack"
              style={{ textAlign: 'left', cursor: 'pointer', border: '1px solid var(--line)' }}
              onClick={() => {
                setValue('profile_type', 'persona_fisica');
                setGatePassed(true);
              }}
            >
              <span className="eyebrow">Persona fisica</span>
              <h3>Benefit, bonus e misure personali</h3>
              <p className="subtle">Ti mostriamo un percorso focalizzato su benefici personali e lavoro, senza trascinarti nel ramo impresa.</p>
            </button>
            <button
              type="button"
              className="card stack"
              style={{ textAlign: 'left', cursor: 'pointer', border: '1px solid var(--line)' }}
              onClick={() => {
                setValue('profile_type', 'startup');
                setGatePassed(true);
              }}
            >
              <span className="eyebrow">Attivita o impresa</span>
              <h3>Incentivi, crediti e misure imprenditoriali</h3>
              <p className="subtle">Percorso per freelance strutturati, startup e PMI con domande su perimetro, investimenti e priorita reali.</p>
            </button>
          </div>
        </div>
      ) : (
        <>
          <section className="panel stack">
            <div className="stack" style={{ gap: '0.45rem' }}>
              <p className="eyebrow">{moduleCopy.eyebrow}</p>
              <h2 style={{ fontSize: '2rem' }}>{moduleCopy.title}</h2>
              <p className="subtle">{moduleCopy.body}</p>
            </div>
            <div className="meta-list">
              <span>Modulo: {moduleCopy.stepLabel}</span>
              <span>Domande attive ora: {currentQuestions.length}</span>
              <span>Sensibili: {currentQuestions.filter((question) => question.sensitive).length}</span>
            </div>
          </section>

          {currentQuestions.length > 0 ? (
            <section className="panel stack">
              <div className="form-grid">
                {currentQuestions.map((question) => (
                  <label className="field" key={question.key}>
                    <span>{question.label}</span>
                    {question.kind === 'boolean' ? (
                      <select {...register(question.key)}>
                        <option value="">Seleziona</option>
                        <option value="true">Si</option>
                        <option value="false">No</option>
                      </select>
                    ) : question.options ? (
                      <select {...register(question.key)}>
                        <option value="">Seleziona</option>
                        {question.options.map((option) => (
                          <option key={option} value={option}>
                            {formatOptionLabel(option)}
                          </option>
                        ))}
                      </select>
                    ) : question.kind === 'text' ? (
                      <textarea {...register(question.key)} />
                    ) : (
                      <input {...register(question.key)} />
                    )}
                    {question.helper_text ? <small className="subtle">{question.helper_text}</small> : null}
                    {question.why_needed ? (
                      <small className="subtle">
                        {question.sensitive ? 'Perche te lo chiediamo adesso: ' : 'Perche lo chiediamo: '}
                        {question.why_needed}
                      </small>
                    ) : null}
                    {question.ask_when_measure_families?.length ? (
                      <small className="subtle">Misure che dipendono da questa risposta: {question.ask_when_measure_families.join(', ')}</small>
                    ) : null}
                    {question.sensitive ? <small className="subtle">Dato sensibile: compare solo in presenza di un blocco o di una famiglia rilevante.</small> : null}
                  </label>
                ))}
              </div>
            </section>
          ) : (
            <section className="panel stack">
              <p className="subtle">
                Nessuna domanda aggiuntiva e necessaria in questo modulo. Puoi andare direttamente ai risultati o tornare piu avanti se il catalogo cambia.
              </p>
            </section>
          )}

          <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap' }}>
            <button className="button" type="submit" disabled={isPending}>
              {isPending
                ? 'Salvataggio...'
                : currentStep === 'core'
                  ? 'Salva il core e mostra i risultati'
                  : currentStep === 'strategic'
                    ? hasConditionalQuestions
                      ? 'Salva e passa alla precisione finale'
                      : 'Salva e vai ai risultati'
                    : 'Aggiorna e vai ai risultati'}
            </button>
            {currentStep !== 'core' ? (
              <Link className="button-secondary" href="/search">
                Salta per ora
              </Link>
            ) : null}
          </div>
          {message ? <div className="banner">{message}</div> : null}
        </>
      )}
    </form>
  );
}

function buildInitialValues(profile: Profile | null): Record<string, string | boolean | null> {
  const factValues = (profile?.fact_values ?? {}) as Record<string, unknown>;
  const values: Record<string, string | boolean | null> = {};
  Object.entries(factValues).forEach(([key, value]) => {
    if (typeof value === 'boolean') {
      values[key] = value ? 'true' : 'false';
      return;
    }
    values[key] = (value as string | boolean | null) ?? null;
  });
  values.profile_type = (values.profile_type as string | undefined) ?? resolveUserType(profile) ?? '';
  values.main_operating_region = (values.main_operating_region as string | undefined) ?? profile?.region ?? '';
  values.legal_form_bucket = (values.legal_form_bucket as string | undefined) ?? profile?.legal_entity_type ?? '';
  values.company_age_or_formation_window =
    (values.company_age_or_formation_window as string | undefined) ?? profile?.company_age_band ?? '';
  values.size_band = (values.size_band as string | undefined) ?? profile?.company_size_band ?? '';
  values.sector_macro_category = (values.sector_macro_category as string | undefined) ?? profile?.sector_code_or_category ?? '';
  values.hiring_interest = normalizeBooleanField(values.hiring_interest, profile?.hiring_intent);
  values.export_investment_intent = normalizeBooleanField(values.export_investment_intent, profile?.export_intent);
  return values;
}

function normalizeBooleanField(current: string | boolean | null | undefined, fallback: boolean | null | undefined) {
  if (current !== undefined && current !== null && current !== '') return current;
  if (fallback === true) return 'true';
  if (fallback === false) return 'false';
  return null;
}

function normalizeValue(question: ProfileQuestion, value: string | boolean | null | undefined): string | boolean | undefined {
  if (value === '' || value === undefined || value === null) return undefined;
  if (question.kind === 'boolean') {
    if (typeof value === 'boolean') return value;
    return value === 'true';
  }
  return value;
}

function formatOptionLabel(option: string): string {
  return option.replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function resolveUserType(profile: Profile | null): string | null {
  const factValues = (profile?.fact_values ?? {}) as Record<string, unknown>;
  return (factValues.profile_type as string | undefined) ?? profile?.user_type ?? null;
}

function nextHref(step: StepKey, hasConditionalQuestions: boolean, entry?: string): string {
  const suffix = entry ? `?entry=${encodeURIComponent(entry)}` : '';
  if (step === 'core') return `/onboarding?step=strategic${entry ? `&entry=${encodeURIComponent(entry)}` : ''}`;
  if (step === 'strategic' && hasConditionalQuestions) {
    return `/onboarding?step=conditional${entry ? `&entry=${encodeURIComponent(entry)}` : ''}`;
  }
  return `/search${suffix}`;
}
