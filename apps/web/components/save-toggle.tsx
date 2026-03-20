'use client';

import { Bookmark, BookmarkCheck } from 'lucide-react';
import { useState, useTransition } from 'react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const API_URL = '/api/proxy';

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
    <Button
      type="button"
      variant={saved ? 'default' : 'secondary'}
      className={cn('min-w-[8.5rem]', !saved && 'bg-white')}
      onClick={onToggle}
      disabled={isPending}
    >
      {saved ? <BookmarkCheck className="size-4" /> : <Bookmark className="size-4" />}
      {isPending ? 'Aggiorno...' : saved ? 'Salvata' : 'Salva'}
    </Button>
  );
}
