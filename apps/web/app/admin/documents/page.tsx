import { redirect } from 'next/navigation';

import { AdminConsoleNav } from '@/components/admin-console-nav';
import { DocumentReviewForm } from '@/components/document-review-form';
import { getAdminDocuments, getSessionUser } from '@/lib/server-api';
import { formatDate } from '@/lib/utils';

type SearchParams = Promise<{
  source_domain?: string;
  role?: string;
  lifecycle_status?: string;
  family_slug?: string;
  document_id?: string;
}>;

export default async function AdminDocumentsPage({ searchParams }: { searchParams: SearchParams }) {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');

  const filters = await searchParams;
  const documents = await getAdminDocuments(filters).catch(() => []);

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Admin</p>
        <h1 style={{ fontSize: '3rem' }}>Documenti ufficiali</h1>
        <p className="subtle">
          Vista unificata tra base legale, decreti, FAQ, portali e pagine operative collegate alle famiglie di misura.
        </p>
        <AdminConsoleNav />
        <form className="form-grid" method="get">
          <label className="field">
            <span>Dominio</span>
            <input defaultValue={filters.source_domain ?? ''} name="source_domain" placeholder="invitalia.it" />
          </label>
          <label className="field">
            <span>Ruolo documento</span>
            <input defaultValue={filters.role ?? ''} name="role" placeholder="legal_basis" />
          </label>
          <label className="field">
            <span>Lifecycle</span>
            <input defaultValue={filters.lifecycle_status ?? ''} name="lifecycle_status" placeholder="open_application" />
          </label>
          <label className="field">
            <span>Famiglia</span>
            <input defaultValue={filters.family_slug ?? ''} name="family_slug" placeholder="smart_start_italia" />
          </label>
          <label className="field">
            <span>Documento</span>
            <input defaultValue={filters.document_id ?? ''} name="document_id" placeholder="uuid documento" />
          </label>
          <div style={{ display: 'flex', alignItems: 'end', gap: '0.8rem' }}>
            <button className="button" type="submit">
              Filtra
            </button>
          </div>
        </form>
      </section>
      <div className="card table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Famiglia</th>
              <th>Dominio</th>
              <th>Titolo</th>
              <th>Ruolo</th>
              <th>Lifecycle</th>
              <th>Relazione</th>
              <th>Data</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={`${document.id}-${document.family_slug}`}>
                <td>{document.family_slug}</td>
                <td>{document.source_domain}</td>
                <td>
                  {document.canonical_url ? (
                    <a href={document.canonical_url} target="_blank" rel="noreferrer">
                      {document.document_title ?? document.canonical_url}
                    </a>
                  ) : (
                    document.document_title ?? 'Documento senza URL canonica'
                  )}
                </td>
                <td>{document.document_role}</td>
                <td>{document.lifecycle_status}</td>
                <td>{document.relationship_type}</td>
                <td>{formatDate(document.created_at)}</td>
                <td>
                  <DocumentReviewForm document={document} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
