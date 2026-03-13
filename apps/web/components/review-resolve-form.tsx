'use client';

import { useState, useTransition } from 'react';

const API_URL = '/api/proxy';

export function ReviewResolveForm({ reviewItemId }: { reviewItemId: string }) {
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  return (
    <div className="stack">
      <button
        className="button-secondary"
        type="button"
        disabled={isPending}
        onClick={() => {
          startTransition(async () => {
            const response = await fetch(`${API_URL}/v1/admin/review-items/${reviewItemId}/resolve`, {
              method: 'POST',
              credentials: 'include',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ resolution_note: 'Risolto da console operativa.' }),
            });
            setMessage(response.ok ? 'Item risolto.' : 'Risoluzione non riuscita.');
          });
        }}
      >
        {isPending ? 'Aggiornamento...' : 'Segna come risolto'}
      </button>
      {message ? <small className="subtle">{message}</small> : null}
    </div>
  );
}
