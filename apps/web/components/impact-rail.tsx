import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { OpportunityCard, ProfileQuestion, ProfileQuestionResponse } from '@/lib/types';

import { OpportunityCard as OpportunityPreviewCard } from './opportunity-card';

export function ImpactRail({
  payload,
  opportunities,
  highlightedQuestions,
}: {
  payload: ProfileQuestionResponse | null;
  opportunities: OpportunityCard[];
  highlightedQuestions: ProfileQuestion[];
}) {
  const progress = payload?.progress_summary;
  const preview = opportunities.slice(0, 2);

  return (
    <div className="grid gap-5 xl:sticky xl:top-28">
      <Card>
        <CardHeader className="pb-4">
          <Badge variant="soft" className="w-fit">Effetto immediato</Badge>
          <CardTitle className="text-4xl leading-[0.95]">Ogni dato in piu puo cambiare ranking e stato.</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 text-sm text-slate-600">
          <p>
            Il motore ricalcola i match dopo ogni salvataggio e rende espliciti i campi ancora mancanti.
          </p>
          {progress ? (
            <div className="grid gap-2 rounded-[1.5rem] border border-border/70 bg-slate-50/80 p-4 text-sm">
              <span>Blocchi chiaribili ora: {progress.blocked_opportunity_count}</span>
              <span>Upgrade potenziali: {progress.upgradable_opportunity_count}</span>
              <span>Completezza profilo: {Math.round(progress.completeness_score)}%</span>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {highlightedQuestions.length > 0 ? (
        <Card>
          <CardHeader className="pb-4">
            <Badge variant="outline" className="w-fit">Prossime leve</Badge>
            <CardTitle className="text-2xl">Le risposte che sbloccano piu opportunita</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {highlightedQuestions.slice(0, 3).map((question) => (
              <div key={question.key} className="rounded-[1.4rem] border border-border/70 bg-white p-4">
                <p className="text-sm font-semibold text-slate-900">{question.label}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">{question.why_needed}</p>
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                  <span>{question.blocking_opportunity_count ?? 0} blocchi</span>
                  <span>{question.upgrade_opportunity_count ?? 0} upgrade</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {preview.length > 0 ? (
        <div className="grid gap-4">
          {preview.map((opportunity) => (
            <OpportunityPreviewCard key={opportunity.id} opportunity={opportunity} />
          ))}
          <Link href="/search" className="button-secondary text-center">
            Apri il catalogo completo
          </Link>
        </div>
      ) : null}
    </div>
  );
}
