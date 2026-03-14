'use client';

import type { FormEvent } from 'react';
import { useState, useTransition } from 'react';

const API_URL = '/api/proxy';

export function MagicLinkForm() {
  const [email, setEmail] = useState('demo@example.com');
  const [message, setMessage] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const isLocalEnvironment = process.env.NODE_ENV !== 'production';

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    startTransition(async () => {
      setMessage(null);
      setPreviewUrl(null);
      try {
        const response = await fetch(`${API_URL}/v1/auth/request-magic-link`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email }),
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
        <p className="eyebrow">Accesso magic link</p>
        <h1 style={{ fontSize: '2.4rem' }}>Accedi senza password</h1>
      </div>
      <p className="lead">
        Inserisci la tua email. {isLocalEnvironment ? 'Se disponibile, vedrai anche un link di anteprima locale.' : 'Riceverai un link di accesso valido per 30 minuti.'}
      </p>
      <label className="field">
        <span>Email</span>
        <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
      </label>
      <button className="button" type="submit" disabled={isPending}>
        {isPending ? 'Invio in corso...' : 'Invia magic link'}
      </button>
      {message ? <div className="banner">{message}</div> : null}
      {previewUrl ? (
        <a className="button-secondary" href={previewUrl}>
          Apri link di anteprima
        </a>
      ) : null}
    </form>
  );
}
