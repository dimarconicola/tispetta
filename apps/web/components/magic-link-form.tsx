'use client';

import type { FormEvent } from 'react';
import { useState, useTransition } from 'react';

const API_URL = '/api/proxy';

type MagicLinkFormProps = {
  eyebrow?: string;
  title?: string;
  lead?: string;
  submitLabel?: string;
  redirectTo?: string | null;
  initialEmail?: string;
};

export function MagicLinkForm({
  eyebrow = 'Accesso magic link',
  title = 'Accedi senza password',
  lead,
  submitLabel = 'Invia magic link',
  redirectTo,
  initialEmail,
}: MagicLinkFormProps) {
  const isLocalEnvironment = process.env.NODE_ENV !== 'production';
  const [email, setEmail] = useState(initialEmail ?? (isLocalEnvironment ? 'demo@example.com' : ''));
  const [message, setMessage] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const resolvedLead =
    lead ??
    `Inserisci la tua email. ${
      isLocalEnvironment ? 'Se disponibile, vedrai anche un link di anteprima locale.' : 'Riceverai un link di accesso valido per 30 minuti.'
    }`;

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    startTransition(async () => {
      setMessage(null);
      setPreviewUrl(null);
      try {
        const response = await fetch(`${API_URL}/v1/auth/request-magic-link`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, redirect_to: redirectTo ?? undefined }),
        });
        const data = (await response.json()) as { detail?: string; message?: string; preview_url?: string | null };
        if (!response.ok) {
          setMessage(data.detail ?? 'Impossibile inviare il magic link in questo momento.');
          return;
        }
        setMessage(data.message ?? 'Link inviato');
        setPreviewUrl(data.preview_url ?? null);
      } catch {
        setMessage('Connessione non riuscita. Riprova tra qualche secondo.');
      }
    });
  }

  return (
    <form className="panel stack" onSubmit={onSubmit}>
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1 style={{ fontSize: '2.4rem' }}>{title}</h1>
      </div>
      <p className="lead">{resolvedLead}</p>
      <label className="field">
        <span>Email</span>
        <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
      </label>
      <button className="button" type="submit" disabled={isPending}>
        {isPending ? 'Invio in corso...' : submitLabel}
      </button>
      {redirectTo ? (
        <p className="subtle">
          Dopo il click entrerai direttamente nel percorso guidato e non nella schermata di accesso generica.
        </p>
      ) : null}
      {message ? <div className="banner">{message}</div> : null}
      {previewUrl ? (
        <a className="button-secondary" href={previewUrl}>
          Apri link di anteprima
        </a>
      ) : null}
    </form>
  );
}
