import Link from 'next/link';
import { redirect } from 'next/navigation';

import { AdminConsoleNav } from '@/components/admin-console-nav';
import { getAdminIngestionRuns, getSessionUser } from '@/lib/server-api';
import { formatDate } from '@/lib/utils';

export default async function AdminIngestionPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');

  const runs = await getAdminIngestionRuns().catch(() => []);

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Admin</p>
        <h1 style={{ fontSize: '3rem' }}>Pipeline di ingestion</h1>
        <p className="subtle">Stato dei job fetch/normalize/extract/verify e diagnostica di esecuzione.</p>
        <AdminConsoleNav />
      </section>
      <div className="card table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Run</th>
              <th>Endpoint</th>
              <th>Stage</th>
              <th>Status</th>
              <th>Start</th>
              <th>Finish</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id}>
                <td>
                  <Link href={`/admin/ingestion/${run.id}`}>{run.id.slice(0, 8)}</Link>
                </td>
                <td>{run.source_endpoint_id.slice(0, 8)}</td>
                <td>{run.stage}</td>
                <td>{run.status}</td>
                <td>{formatDate(run.started_at)}</td>
                <td>{formatDate(run.finished_at ?? null)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
