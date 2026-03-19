import { redirect } from 'next/navigation';

import { AdminConsoleNav } from '@/components/admin-console-nav';
import { ReviewResolveForm } from '@/components/review-resolve-form';
import { getAdminReviewItems, getSessionUser } from '@/lib/server-api';

export default async function AdminReviewPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');

  const items = await getAdminReviewItems().catch(() => []);

  const hrefForItem = (item: (typeof items)[number]) => {
    const payload = item.payload ?? {};
    const documentId = typeof payload.normalized_document_id === 'string' ? payload.normalized_document_id : null;
    if (documentId) {
      return `/admin/documents?document_id=${documentId}`;
    }
    if (item.related_entity_type === 'opportunity') {
      return `/admin/opportunities/${item.related_entity_id}`;
    }
    return '/admin/ingestion';
  };

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Admin</p>
        <h1 style={{ fontSize: '3rem' }}>Review queue</h1>
        <p className="subtle">Eccezioni, publish pending e conflitti da risolvere senza accesso diretto al database.</p>
        <AdminConsoleNav />
      </section>
      <div className="grid cards-2">
        {items.map((item) => (
          <article className="card stack" key={item.id}>
            <div>
              <p className="eyebrow">{item.item_type}</p>
              <h2 style={{ fontSize: '1.8rem' }}>{item.title}</h2>
            </div>
            <p className="subtle">{item.description}</p>
            <div className="meta-list">
              <span>Entity: {item.related_entity_type}</span>
              <span>Status: {item.status}</span>
            </div>
            <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap' }}>
              <a className="button-secondary" href={hrefForItem(item)}>
                Apri contesto
              </a>
              <ReviewResolveForm reviewItemId={item.id} />
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
