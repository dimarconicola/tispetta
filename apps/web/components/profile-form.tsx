'use client';

import { useMemo, useState, useTransition } from 'react';
import { useForm } from 'react-hook-form';

import type { Profile, ProfileQuestion } from '@/lib/types';

const API_URL = '/api/proxy';

export function ProfileForm({ profile, questions }: { profile: Profile | null; questions: ProfileQuestion[] }) {
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const { register, handleSubmit, watch } = useForm<Profile>({
    defaultValues: profile ?? undefined,
  });

  const userType = watch('user_type') ?? profile?.user_type ?? 'startup';
  const visibleQuestions = useMemo(
    () => questions.filter((question) => !question.audience || question.audience.includes(userType ?? 'startup')),
    [questions, userType]
  );

  const grouped = visibleQuestions.reduce<Record<number, ProfileQuestion[]>>((acc, question) => {
    const bucket = acc[question.step] ?? [];
    bucket.push(question);
    acc[question.step] = bucket;
    return acc;
  }, {});

  return (
    <form
      className="stack"
      onSubmit={handleSubmit((values) => {
        startTransition(async () => {
          const normalized = {
            ...values,
            business_exists: normalizeBoolean(values.business_exists as unknown as string | boolean | null),
            hiring_intent: normalizeBoolean(values.hiring_intent as unknown as string | boolean | null),
            innovation_intent: normalizeBoolean(values.innovation_intent as unknown as string | boolean | null),
            sustainability_intent: normalizeBoolean(values.sustainability_intent as unknown as string | boolean | null),
            export_intent: normalizeBoolean(values.export_intent as unknown as string | boolean | null),
          };
          const response = await fetch(`${API_URL}/v1/profile`, {
            method: 'PUT',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(normalized),
          });
          setMessage(response.ok ? 'Profilo aggiornato e matching ricalcolato.' : 'Aggiornamento non riuscito.');
        });
      })}
    >
      {Object.entries(grouped).map(([step, items]) => (
        <section className="panel stack" key={step}>
          <div>
            <p className="eyebrow">Step {step}</p>
            <h2 style={{ fontSize: '2rem' }}>
              {step === '1'
                ? 'Profilo base'
                : step === '2'
                  ? 'Informazioni essenziali'
                  : step === '4'
                    ? 'Obiettivi e priorita'
                    : 'Dettagli aggiuntivi'}
            </h2>
          </div>
          <div className="form-grid">
            {items.map((question) => (
              <label className="field" key={question.key}>
                <span>{question.label}</span>
                {question.options ? (
                  <select {...register(question.key as keyof Profile)}>
                    <option value="">Seleziona</option>
                    {question.options.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input {...register(question.key as keyof Profile)} />
                )}
                {question.helper_text ? <small className="subtle">{question.helper_text}</small> : null}
              </label>
            ))}
          </div>
        </section>
      ))}
      <button className="button" type="submit" disabled={isPending}>
        {isPending ? 'Salvataggio...' : 'Salva profilo'}
      </button>
      {message ? <div className="banner">{message}</div> : null}
    </form>
  );
}

function normalizeBoolean(value: string | boolean | null | undefined): boolean | null | undefined {
  if (value === '' || value === undefined) return undefined;
  if (value === null) return null;
  if (typeof value === 'boolean') return value;
  return value === 'true';
}
