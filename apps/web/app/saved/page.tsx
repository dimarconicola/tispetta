import Link from 'next/link';
import { redirect } from 'next/navigation';

import { FilterChips } from '@/components/filter-chips';
import { OpportunityCard } from '@/components/opportunity-card';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getOpportunities, getSessionUser } from '@/lib/server-api';
import type { OpportunityCard as OpportunityCardType } from '@/lib/types';

const STATUS_ORDER = ['confirmed', 'likely', 'unclear', 'not_eligible'];
const STATUS_LABELS: Record<string, { eyebrow: string; title: string; body: string }> = {
  confirmed: {
    eyebrow: 'Confermate',
    title: 'Idonee con i tuoi dati attuali',
    body: 'Sono le schede piu solide con il profilo attuale.',
  },
  likely: {
    eyebrow: 'Compatibili',
    title: 'Coerenti, ma da rifinire',
    body: 'Hanno buon fit, ma puoi confermarle con poche risposte mirate.',
  },
  unclear: {
    eyebrow: 'Da chiarire',
    title: 'Serve piu contesto',
    body: 'Il motore non ha ancora i dati necessari per dare uno stato piu forte.',
  },
  not_eligible: {
    eyebrow: 'Fuori profilo',
    title: 'Oggi non risultano coerenti',
    body: 'Le puoi tenere come promemoria, ma con i dati attuali non emergono come adatte.',
  },
};

function sortByDeadline(items: OpportunityCardType[]): OpportunityCardType[] {
  return [...items].sort((a, b) => {
    if (!a.deadline_date && !b.deadline_date) return 0;
    if (!a.deadline_date) return 1;
    if (!b.deadline_date) return -1;
    return new Date(a.deadline_date).getTime() - new Date(b.deadline_date).getTime();
  });
}

const SCOPE_ITEMS = [
  { label: 'Personale', value: 'personal' },
  { label: 'Attivita', value: 'business' },
];

export default async function SavedPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const scope = typeof params.scope === 'string' ? params.scope : '';
  const user = await getSessionUser().catch(() => null);
  if (!user) {
    redirect('/auth/sign-in');
  }

  const items = await getOpportunities({ saved_only: true, scope: scope || undefined }).catch(() => []);
  const grouped = STATUS_ORDER.reduce<Record<string, OpportunityCardType[]>>((acc, status) => {
    acc[status] = sortByDeadline(items.filter((item) => item.match_status === status));
    return acc;
  }, {} as Record<string, OpportunityCardType[]>);
  const unmatched = items.filter((item) => !item.match_status);

  return (
    <div className="grid gap-8 pb-8">
      <section className="grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.85fr)]">
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="soft" className="w-fit">Salvate</Badge>
            <CardTitle className="text-5xl leading-[0.95]">La tua shortlist da monitorare.</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-base leading-7 text-slate-600">
            <p>Le opportunita salvate restano ordinate per stato e urgenza, cosi puoi rientrare e capire subito dove intervenire.</p>
            <FilterChips items={SCOPE_ITEMS} active={scope || null} buildHref={(value) => `/saved${value ? `?scope=${encodeURIComponent(value)}` : ''}`} />
            {items.length === 0 ? (
              <Link href="/search" className="button-secondary w-fit">
                Esplora il catalogo
              </Link>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="gap-3">
            <Badge variant="outline" className="w-fit">Snapshot</Badge>
            <CardTitle className="text-3xl">{items.length} opportunita salvate</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm text-slate-600">
            <span>{(grouped.confirmed ?? []).length} confermate</span>
            <span>{(grouped.likely ?? []).length} compatibili</span>
            <span>{(grouped.unclear ?? []).length} da chiarire</span>
          </CardContent>
        </Card>
      </section>

      {items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-wrap items-center justify-between gap-4 py-8 text-sm text-slate-600">
            <span>Nessuna opportunita salvata per ora. Usa il catalogo per trovare quelle davvero rilevanti.</span>
            <Link href="/search" className="button">
              Vai alla ricerca
            </Link>
          </CardContent>
        </Card>
      ) : (
        <>
          {STATUS_ORDER.filter((status) => (grouped[status] ?? []).length > 0).map((status) => {
            const meta = STATUS_LABELS[status] ?? {
              eyebrow: status,
              title: status,
              body: '',
            };
            const cards = grouped[status] ?? [];
            return (
              <section key={status} className="grid gap-5">
                <div className="flex flex-col gap-3 border-b border-slate-200 pb-4 md:flex-row md:items-end md:justify-between">
                  <div>
                    <p className="eyebrow">{meta.eyebrow}</p>
                    <h2 className="section-title">{meta.title}</h2>
                    <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">{meta.body}</p>
                  </div>
                  <span className="text-sm text-slate-500">{cards.length}</span>
                </div>
                <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
                  {cards.map((opportunity) => (
                    <OpportunityCard key={opportunity.id} opportunity={opportunity} />
                  ))}
                </div>
              </section>
            );
          })}

          {unmatched.length > 0 ? (
            <section className="grid gap-5">
              <div className="flex flex-col gap-3 border-b border-slate-200 pb-4 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="eyebrow">Da valutare</p>
                  <h2 className="section-title">Completa il profilo per vederne il match</h2>
                </div>
                <span className="text-sm text-slate-500">{unmatched.length}</span>
              </div>
              <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
                {unmatched.map((opportunity) => (
                  <OpportunityCard key={opportunity.id} opportunity={opportunity} />
                ))}
              </div>
            </section>
          ) : null}
        </>
      )}
    </div>
  );
}
