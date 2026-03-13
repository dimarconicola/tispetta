import { redirect } from 'next/navigation';

import { AdminConsoleNav } from '@/components/admin-console-nav';
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
