import Link from 'next/link';
import { redirect } from 'next/navigation';

import { OpportunityCard } from '@/components/opportunity-card';
import { getOpportunities, getSessionUser } from '@/lib/server-api';
import type { OpportunityCard as OpportunityCardType } from '@/lib/types';

const STATUS_ORDER = ['confirmed', 'likely', 'unclear', 'not_eligible'];
const STATUS_LABELS: Record<string, { eyebrow: string; title: string }> = {
  confirmed: { eyebrow: 'Confermate', title: 'Idonee con i tuoi dati attuali' },
  likely: { eyebrow: 'Probabili', title: 'Promettenti, con qualche dato mancante' },
  unclear: { eyebrow: 'Da chiarire', title: 'Criteri non ancora verificabili' },
  not_eligible: { eyebrow: 'Non idonee', title: 'Non corrispondenti al profilo attuale' },
};

function sortByDeadline(items: OpportunityCardType[]): OpportunityCardType[] {
  return [...items].sort((a, b) => {
    if (!a.deadline_date && !b.deadline_date) return 0;
    if (!a.deadline_date) return 1;
    if (!b.deadline_date) return -1;
    return new Date(a.deadline_date).getTime() - new Date(b.deadline_date).getTime();
  });
}

export default async function SavedPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) {
    redirect('/auth/sign-in');
  }

  const items = await getOpportunities({ saved_only: true }).catch(() => []);

  const grouped = STATUS_ORDER.reduce<Record<string, OpportunityCardType[]>>((acc, status) => {
    acc[status] = sortByDeadline(items.filter((item) => item.match_status === status));
    return acc;
  }, {} as Record<string, OpportunityCardType[]>);
  const unmatched = items.filter((item) => !item.match_status);

  const confirmedCount = (grouped.confirmed ?? []).length;
  const hasItems = items.length > 0;

  return (
    <div className="stack">
      <section className="panel stack">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <p className="eyebrow">Salvate — {items.length} opportunita</p>
            <h1 style={{ fontSize: '3rem' }}>La tua shortlist da monitorare.</h1>
            <p className="subtle">Opportunita salvate, ordinate per stato di match e scadenza.</p>
          </div>
          {confirmedCount > 0 ? (
            <div style={{ textAlign: 'right' }}>
              <strong style={{ fontSize: '2.4rem' }}>{confirmedCount}</strong>
              <p className="subtle" style={{ fontSize: '0.85rem' }}>confermate</p>
            </div>
          ) : null}
        </div>
        {!hasItems ? (
          <Link href="/search" className="button-secondary" style={{ alignSelf: 'flex-start' }}>
            Esplora il catalogo
          </Link>
        ) : null}
      </section>

      {!hasItems ? (
        <div className="banner">Nessuna opportunita salvata per ora. Usa il catalogo per trovarne di rilevanti.</div>
      ) : (
        <>
          {STATUS_ORDER.filter((status) => (grouped[status] ?? []).length > 0).map((status) => {
            const statusMeta = STATUS_LABELS[status] ?? { eyebrow: status, title: status };
            return (
              <section className="section" key={status}>
                <div className="section-header">
                  <div>
                    <p className="eyebrow">{statusMeta.eyebrow}</p>
                    <h2 className="section-title">{statusMeta.title}</h2>
                  </div>
                  <span className="subtle" style={{ fontSize: '0.9rem' }}>{(grouped[status] ?? []).length}</span>
                </div>
                <div className="grid cards-3">
                  {(grouped[status] ?? []).map((opportunity) => (
                    <OpportunityCard key={opportunity.id} opportunity={opportunity} />
                  ))}
                </div>
              </section>
            );
          })}
          {unmatched.length > 0 ? (
            <section className="section">
              <div className="section-header">
                <div>
                  <p className="eyebrow">Da valutare</p>
                  <h2 className="section-title">Completa il profilo per vedere il match</h2>
                </div>
                <span className="subtle" style={{ fontSize: '0.9rem' }}>{unmatched.length}</span>
              </div>
              <div className="grid cards-3">
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
