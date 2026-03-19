'use client';

import { useState, useTransition } from 'react';

const API_URL = '/api/proxy';

export function OpportunityPublishControls({
  opportunityId,
  recordStatus,
}: {
  opportunityId: string;
  recordStatus: string;
}) {
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const isPublished = recordStatus === 'published';

  return (
    <div className="stack" style={{ gap: '0.8rem' }}>
      <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap' }}>
        <button
          className="button"
          disabled={isPending || isPublished}
          type="button"
          onClick={() => {
            startTransition(async () => {
              setMessage(null);
              const response = await fetch(`${API_URL}/v1/admin/opportunities/${opportunityId}/publish`, {
                method: 'POST',
                credentials: 'include',
              });
              setMessage(response.ok ? 'Opportunity pubblicata.' : 'Publish non riuscito.');
            });
          }}
        >
          {isPending && !isPublished ? 'Pubblicazione...' : 'Pubblica'}
        </button>
        <button
          className="button-secondary"
          disabled={isPending || !isPublished}
          type="button"
          onClick={() => {
            startTransition(async () => {
              setMessage(null);
              const response = await fetch(`${API_URL}/v1/admin/opportunities/${opportunityId}/unpublish`, {
                method: 'POST',
                credentials: 'include',
              });
              setMessage(response.ok ? 'Opportunity ritirata.' : 'Unpublish non riuscito.');
            });
          }}
        >
          {isPending && isPublished ? 'Aggiornamento...' : 'Ritira'}
        </button>
      </div>
      {message ? <small className="subtle">{message}</small> : null}
    </div>
  );
}
