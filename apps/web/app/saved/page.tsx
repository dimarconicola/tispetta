import { redirect } from 'next/navigation';

import { OpportunityCard } from '@/components/opportunity-card';
import { getOpportunities, getSessionUser } from '@/lib/server-api';

export default async function SavedPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) {
    redirect('/auth/sign-in');
  }

  const items = await getOpportunities({ saved_only: true }).catch(() => []);

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Salvate</p>
        <h1 style={{ fontSize: '3rem' }}>La tua shortlist da monitorare.</h1>
        <p className="subtle">Qui arrivano le opportunita che vuoi tenere sotto controllo per scadenze o aggiornamenti di fonte.</p>
      </section>
      <div className="grid cards-3">
        {items.length ? items.map((opportunity) => <OpportunityCard key={opportunity.id} opportunity={opportunity} />) : <div className="banner">Nessuna opportunita salvata per ora.</div>}
      </div>
    </div>
  );
}
