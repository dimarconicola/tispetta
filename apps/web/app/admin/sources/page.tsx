import { redirect } from 'next/navigation';

import { getAdminSources, getSessionUser } from '@/lib/server-api';

export default async function AdminSourcesPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');

  const sources = await getAdminSources().catch(() => []);

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Admin</p>
        <h1 style={{ fontSize: '3rem' }}>Registro fonti</h1>
        <p className="subtle">Set controllato di fonti Tier 1 con priorita operative e frequenze di refresh.</p>
      </section>
      <div className="card table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Fonte</th>
              <th>Tipo</th>
              <th>Crawl</th>
              <th>Frequenza</th>
              <th>Trust</th>
              <th>Stato</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr key={source.id}>
                <td>{source.source_name}</td>
                <td>{source.source_type}</td>
                <td>{source.crawl_method}</td>
                <td>{source.crawl_frequency}</td>
                <td>{source.trust_level}</td>
                <td>{source.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
