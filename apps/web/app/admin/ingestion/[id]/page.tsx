import Link from 'next/link';
import { redirect } from 'next/navigation';

import { AdminConsoleNav } from '@/components/admin-console-nav';
import { getAdminIngestionRun, getSessionUser } from '@/lib/server-api';

export default async function AdminIngestionRunPage({ params }: { params: Promise<{ id: string }> }) {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');

  const { id } = await params;
  const run = await getAdminIngestionRun(id).catch(() => null);
  if (!run) redirect('/admin/ingestion');

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Admin</p>
        <h1 style={{ fontSize: '3rem' }}>Dettaglio ingestion run</h1>
        <p className="subtle">Diagnostica completa per fetch, normalize, extract, review routing e collegamenti alla console.</p>
        <AdminConsoleNav />
      </section>
      <section className="grid cards-2">
        <article className="card stack">
          <h2>Contesto</h2>
          <div className="meta-list">
            <span>Run: {run.id}</span>
            <span>Fonte: {run.source_name}</span>
            <span>Endpoint: {run.endpoint_name}</span>
            <span>Stage: {run.stage}</span>
            <span>Status: {run.status}</span>
          </div>
          <a href={run.endpoint_url} target="_blank" rel="noreferrer">
            {run.endpoint_url}
          </a>
        </article>
        <article className="card stack">
          <h2>Collegamenti</h2>
          <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap' }}>
            {run.normalized_document_id ? (
              <Link className="button-secondary" href={`/admin/documents?document_id=${run.normalized_document_id}`}>
                Apri documento
              </Link>
            ) : null}
            {run.review_item_id ? (
              <Link className="button-secondary" href="/admin/review">
                Apri review queue
              </Link>
            ) : null}
            <Link className="button-secondary" href="/admin/ingestion">
              Torna ai run
            </Link>
          </div>
        </article>
      </section>
      <section className="card stack">
        <h2>Diagnostica</h2>
        <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{JSON.stringify(run.diagnostics ?? {}, null, 2)}</pre>
      </section>
    </div>
  );
}
