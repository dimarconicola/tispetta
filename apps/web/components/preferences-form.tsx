'use client';

import { useState, useTransition } from 'react';
import { useForm } from 'react-hook-form';

import type { NotificationPreferences } from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export function PreferencesForm({ preferences }: { preferences: NotificationPreferences | null }) {
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const { register, handleSubmit } = useForm<NotificationPreferences>({ defaultValues: preferences ?? undefined });

  return (
    <form
      className="panel stack"
      onSubmit={handleSubmit((values) => {
        startTransition(async () => {
          const response = await fetch(`${API_URL}/v1/notifications/preferences`, {
            method: 'PUT',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(values),
          });
          setMessage(response.ok ? 'Preferenze salvate.' : 'Salvataggio non riuscito.');
        });
      })}
    >
      <div>
        <p className="eyebrow">Notifiche email</p>
        <h2 style={{ fontSize: '2rem' }}>Controlla ritmo e tipologia degli alert</h2>
      </div>
      {[
        ['email_enabled', 'Abilita email di prodotto'],
        ['new_opportunity_alerts', 'Nuove opportunita pertinenti'],
        ['deadline_reminders', 'Promemoria scadenze'],
        ['source_change_digests', 'Digest modifiche fonti'],
        ['weekly_profile_nudges', 'Promemoria completamento profilo'],
      ].map(([key, label]) => (
        <label key={key} style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
          <input type="checkbox" {...register(key as keyof NotificationPreferences)} />
          <span>{label}</span>
        </label>
      ))}
      <button className="button" type="submit" disabled={isPending}>
        {isPending ? 'Salvataggio...' : 'Aggiorna preferenze'}
      </button>
      {message ? <div className="banner">{message}</div> : null}
    </form>
  );
}
