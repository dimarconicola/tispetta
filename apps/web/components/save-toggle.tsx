'use client';

import { useState, useTransition } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export function SaveToggle({ opportunityId, initialSaved }: { opportunityId: string; initialSaved: boolean }) {
  const [saved, setSaved] = useState(initialSaved);
  const [isPending, startTransition] = useTransition();

  function onToggle() {
    startTransition(async () => {
      const nextSaved = !saved;
      const response = await fetch(`${API_URL}/v1/opportunities/${opportunityId}/save`, {
        method: nextSaved ? 'POST' : 'DELETE',
        credentials: 'include',
      });
      if (response.ok) {
        setSaved(nextSaved);
      }
    });
  }

  return (
    <button type="button" className="button" onClick={onToggle} disabled={isPending}>
      {saved ? 'Salvata' : 'Salva'}
    </button>
  );
}
