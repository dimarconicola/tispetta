'use client';

import { useMemo, useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';

import type { Profile, ProfileQuestion } from '@/lib/types';

const API_URL = '/api/proxy';

const MODULE_COPY: Record<string, { eyebrow: string; title: string; body: string }> = {
  core_entity: {
    eyebrow: 'Core Entity',
    title: 'Fatti stabili che definiscono il tuo perimetro',
    body: 'Queste risposte servono per evitare falsi positivi sulle famiglie di misura davvero rilevanti.',
  },
  strategic_intent: {
    eyebrow: 'Strategic Intent',
    title: 'Progetti e priorita che cambiano il ranking',
    body: 'Qui distinguiamo interesse generico da iniziative concrete su export, digitale, energia e hiring.',
  },
  conditional_accuracy: {
    eyebrow: 'Conditional Accuracy',
    title: 'Domande attivate solo quando aumentano la precisione',
    body: 'Le chiediamo solo se servono a sbloccare o chiarire misure specifiche.',
  },
};

export function ProfileForm({ profile, questions }: { profile: Profile | null; questions: ProfileQuestion[] }) {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [gatePassed, setGatePassed] = useState(Boolean(profile?.user_type));
  const initialValues = useMemo(() => buildInitialValues(profile), [profile]);
  const { register, handleSubmit, watch, setValue } = useForm<Record<string, string | boolean | null>>({
    defaultValues: initialValues,
  });

  const userType = (watch('profile_type') as string | undefined) || (profile?.fact_values?.profile_type as string | undefined) || profile?.user_type || 'startup';
  const visibleQuestions = useMemo(
    () => questions.filter((question) => !question.audience || question.audience.includes(userType)),
    [questions, userType]
  );

  const grouped = visibleQuestions.reduce<Record<string, ProfileQuestion[]>>((acc, question) => {
    const bucket = acc[question.module ?? 'core_entity'] ?? [];
    bucket.push(question);
    acc[question.module ?? 'core_entity'] = bucket;
    return acc;
  }, {});

  return (
    <form
      className="stack"
      onSubmit={handleSubmit((values) => {
        startTransition(async () => {
          const normalized = {
            fact_values: Object.fromEntries(
              visibleQuestions
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
          setMessage(response.ok ? 'Profilo aggiornato e matching ricalcolato.' : 'Aggiornamento non riuscito.');
          if (response.ok) {
            router.push('/');
          }
        });
      })}
    >
      {!gatePassed ? (
        <div className="stack">
          <div className="panel stack">
            <p className="eyebrow">Come vuoi usare Tispetta?</p>
            <h2 style={{ fontSize: '2rem' }}>Stai cercando qualcosa per te o per un'attivita?</h2>
            <p className="subtle">La risposta cambia le domande che ti facciamo: poche e mirate.</p>
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
              <h3>Per me — bonus, detrazioni e benefici personali</h3>
              <p className="subtle">Assegno Unico, bonus nido, detrazione figli, NASpI, regime forfettario, bonus casa. Tutto quello che ti spetta come privato, dipendente o freelance che inizia.</p>
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
              <h3>Per la mia attivita — incentivi, crediti e misure imprenditoriali</h3>
              <p className="subtle">Crediti R&S, Transizione 5.0, Smart & Start, voucher digitale, incentivi assunzioni, export. Misure per freelance strutturati, startup e PMI.</p>
            </button>
          </div>
        </div>
      ) : (
        <>
          {Object.entries(grouped).map(([module, items]) => (
            <section className="panel stack" key={module}>
              <div>
                <p className="eyebrow">{MODULE_COPY[module]?.eyebrow ?? 'Profilo'}</p>
                <h2 style={{ fontSize: '2rem' }}>{MODULE_COPY[module]?.title ?? 'Profilo'}</h2>
                <p className="subtle">{MODULE_COPY[module]?.body}</p>
              </div>
              <div className="form-grid">
                {items.map((question) => (
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
                    {question.why_needed ? <small className="subtle">Perche lo chiediamo: {question.why_needed}</small> : null}
                    {question.ask_when_measure_families?.length ? (
                      <small className="subtle">Famiglie collegate: {question.ask_when_measure_families.join(', ')}</small>
                    ) : null}
                    {question.sensitive ? <small className="subtle">Dato sensibile: mostrato solo quando serve davvero.</small> : null}
                  </label>
                ))}
              </div>
            </section>
          ))}
          <button className="button" type="submit" disabled={isPending}>
            {isPending ? 'Salvataggio...' : 'Salva profilo'}
          </button>
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
  values.profile_type = (values.profile_type as string | undefined) ?? profile?.user_type ?? '';
  values.main_operating_region = (values.main_operating_region as string | undefined) ?? profile?.region ?? '';
  values.legal_form_bucket = (values.legal_form_bucket as string | undefined) ?? profile?.legal_entity_type ?? '';
  values.company_age_or_formation_window =
    (values.company_age_or_formation_window as string | undefined) ?? profile?.company_age_band ?? '';
  values.size_band = (values.size_band as string | undefined) ?? profile?.company_size_band ?? '';
  values.sector_macro_category = (values.sector_macro_category as string | undefined) ?? profile?.sector_code_or_category ?? '';
  values.hiring_interest = (values.hiring_interest as boolean | undefined) ?? profile?.hiring_intent ?? null;
  values.export_investment_intent = (values.export_investment_intent as boolean | undefined) ?? profile?.export_intent ?? null;
  return values;
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
  return option
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
