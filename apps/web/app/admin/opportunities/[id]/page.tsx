import { redirect } from 'next/navigation';

import { AdminConsoleNav } from '@/components/admin-console-nav';
import { OpportunityPublishControls } from '@/components/opportunity-publish-controls';
import { getAdminOpportunityDiff, getSessionUser } from '@/lib/server-api';

export default async function AdminOpportunityDiffPage({ params }: { params: Promise<{ id: string }> }) {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');

  const { id } = await params;
  const diff = await getAdminOpportunityDiff(id).catch(() => null);

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Admin</p>
        <h1 style={{ fontSize: '3rem' }}>Diff opportunita</h1>
        <p className="subtle">Confronto rapido tra versione corrente e versione precedente.</p>
        <AdminConsoleNav />
      </section>
      <section className="grid cards-2">
        <article className="card stack">
          <h2>Stato operativo</h2>
          <div className="meta-list">
            <span>Titolo: {String(diff?.opportunity_title ?? 'N/D')}</span>
            <span>Record status: {String(diff?.record_status ?? 'N/D')}</span>
            <span>Famiglia misura: {String(diff?.measure_family_slug ?? 'N/D')}</span>
            <span>Rule attiva: {String(diff?.active_rule_id ?? 'N/D')}</span>
          </div>
          <OpportunityPublishControls opportunityId={id} recordStatus={String(diff?.record_status ?? 'draft')} />
        </article>
        <article className="card stack">
          <h2>Esito fixture</h2>
          <div className="meta-list">
            <span>Passano: {String((diff?.rule_test_summary as { passed?: boolean } | undefined)?.passed ?? false)}</span>
            <span>Totali: {String((diff?.rule_test_summary as { total?: number } | undefined)?.total ?? 0)}</span>
            <span>Fallite: {String((diff?.rule_test_summary as { failed?: number } | undefined)?.failed ?? 0)}</span>
          </div>
        </article>
      </section>
      <div className="grid cards-2">
        <article className="card stack">
          <h2>Versione corrente</h2>
          <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{JSON.stringify(diff?.current ?? {}, null, 2)}</pre>
        </article>
        <article className="card stack">
          <h2>Versione precedente</h2>
          <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{JSON.stringify(diff?.previous ?? {}, null, 2)}</pre>
        </article>
      </div>
      <div className="banner">Campi modificati: {Array.isArray(diff?.changed_fields) ? diff?.changed_fields.join(', ') : 'nessuna informazione'}</div>
    </div>
  );
}
