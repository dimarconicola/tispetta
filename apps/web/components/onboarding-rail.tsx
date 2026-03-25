import Link from 'next/link';
import { ArrowRight } from 'lucide-react';

import type { ProfileQuestionResponse } from '@/lib/types';

import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

export function OnboardingRail({
  payload,
}: {
  payload: ProfileQuestionResponse | null;
}) {
  const summary = payload?.results_summary;

  return (
    <div className="grid gap-4 xl:sticky xl:top-28">
      <Card>
        <CardHeader className="pb-4">
          <Badge variant="soft" className="w-fit">Stato profilo</Badge>
          <CardTitle className="text-3xl leading-[0.95]">{summary?.profile_state ?? 'Profilo in preparazione'}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm leading-7 text-slate-600">
          <p>
            {summary?.ready
              ? `Hai gia ${summary.total_matches} schede leggibili. Il passaggio corrente serve solo a rendere il feed piu preciso.`
              : 'Completa il passaggio attuale e poi vedrai subito il primo riepilogo utile.'}
          </p>
          {summary?.next_focus_labels?.length ? (
            <div className="grid gap-2 rounded-[1.25rem] border border-border/70 bg-slate-50/85 p-4">
              <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Prossimi temi</span>
              <span className="text-sm font-medium text-slate-900">{summary.next_focus_labels.join(' · ')}</span>
            </div>
          ) : null}
          <Link href="/search" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition-colors hover:text-primary">
            Vedi il catalogo completo
            <ArrowRight className="size-4" />
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
