import Link from 'next/link';

import type { ProfileQuestionResponse } from '@/lib/types';

import { OpportunityCard } from './opportunity-card';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

export function OnboardingRail({
  payload,
}: {
  payload: ProfileQuestionResponse | null;
}) {
  const summary = payload?.results_summary;
  const preview = summary?.top_matches?.slice(0, 2) ?? [];

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
              ? `Hai gia ${summary.total_matches} misure leggibili. Quelle ancora aperte si chiudono con pochi passaggi mirati.`
              : 'Completa il passaggio attuale e il riepilogo si aggiorna con le prime misure da guardare.'}
          </p>
          {summary?.next_focus_labels?.length ? (
            <div className="grid gap-2 rounded-[1.25rem] border border-border/70 bg-slate-50/85 p-4">
              <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Dopo questo passaggio</span>
              <span className="text-sm font-medium text-slate-900">{summary.next_focus_labels.join(' · ')}</span>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {preview.length ? (
        <div className="grid gap-4">
          {preview.map((opportunity) => (
            <OpportunityCard key={opportunity.id} opportunity={opportunity} />
          ))}
          <Link href="/search" className="button-secondary text-center">
            Apri il catalogo completo
          </Link>
        </div>
      ) : null}
    </div>
  );
}
