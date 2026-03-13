'use client';

import { useRouter } from 'next/navigation';
import { useState, useTransition } from 'react';

import type { BootstrapRunResult } from '@/lib/types';

const API_URL = '/api/proxy';

export function BootstrapRunner() {
  const router = useRouter();
  const [result, setResult] = useState<BootstrapRunResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  return (
    <div className="stack">
      <button
        type="button"
        className="button"
        disabled={isPending}
        onClick={() => {
          startTransition(async () => {
            setMessage(null);
            const response = await fetch(`${API_URL}/v1/admin/bootstrap/run`, {
              method: 'POST',
              credentials: 'include',
            });
            if (!response.ok) {
              setMessage('Bootstrap non riuscito.');
              return;
            }
            const payload = (await response.json()) as BootstrapRunResult;
            setResult(payload);
            setMessage(payload.review_message);
            router.refresh();
          });
        }}
      >
        {isPending ? 'Aggiornamento corpus...' : 'Esegui bootstrap'}
      </button>
      {message ? <small className="subtle">{message}</small> : null}
      {result ? (
        <div className="banner">
          <strong>Corpus aggiornato</strong>
          <div className="meta-list" style={{ marginTop: '0.8rem' }}>
            <span>Famiglie: {result.measure_families_seeded}</span>
            <span>Documenti: {result.documents_seeded}</span>
            <span>Fatti: {result.facts_seeded}</span>
            <span>Righe survey: {result.coverage_rows}</span>
          </div>
        </div>
      ) : null}
    </div>
  );
}
