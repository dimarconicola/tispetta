import { redirect } from 'next/navigation';

import { AdminConsoleNav } from '@/components/admin-console-nav';
import { BootstrapRunner } from '@/components/bootstrap-runner';
import { getAdminSurveyCoverage, getSessionUser } from '@/lib/server-api';

export default async function AdminSurveyCoveragePage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');

  const coverage = await getAdminSurveyCoverage().catch(() => null);

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Admin</p>
        <h1 style={{ fontSize: '3rem' }}>Copertura survey</h1>
        <p className="subtle">
          Il questionario non e piu definito a mano: ogni domanda nasce dal corpus ufficiale, dal suo peso di copertura e dal potere di ridurre ambiguita.
        </p>
        <AdminConsoleNav />
      </section>
      <section className="grid cards-2">
        <article className="card stack">
          <h2 style={{ fontSize: '1.6rem' }}>Snapshot corrente</h2>
          <div className="meta-list">
            <span>Snapshot key: {coverage?.snapshot_key ?? 'n/d'}</span>
            <span>Famiglie totali: {coverage?.total_measure_families ?? 0}</span>
            <span>Famiglie attive: {coverage?.total_active_measure_families ?? 0}</span>
            <span>Fatti in copertura: {coverage?.rows.length ?? 0}</span>
          </div>
        </article>
        <article className="card stack">
          <h2 style={{ fontSize: '1.6rem' }}>Bootstrap corpus</h2>
          <p className="subtle">
            Riesegue il bootstrap seed-driven del corpus nazionale e ricalcola i pesi del questionario in base alle famiglie di misura attive.
          </p>
          <BootstrapRunner />
        </article>
      </section>
      <div className="card table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Fatto</th>
              <th>Modulo</th>
              <th>Coverage</th>
              <th>Ambiguita</th>
              <th>Hard</th>
              <th>Project</th>
              <th>Person</th>
              <th>Ranking</th>
              <th>Gate</th>
            </tr>
          </thead>
          <tbody>
            {(coverage?.rows ?? []).map((row) => (
              <tr key={row.fact_key}>
                <td>
                  <strong>{row.label}</strong>
                  <div className="subtle">{row.fact_key}</div>
                </td>
                <td>{row.module}</td>
                <td>{row.coverage_weight}</td>
                <td>{row.ambiguity_reduction_score}</td>
                <td>{row.hard_requirement_count}</td>
                <td>{row.project_requirement_count}</td>
                <td>{row.person_requirement_count}</td>
                <td>{row.ranking_requirement_count}</td>
                <td>{row.ask_when_measure_families.join(', ') || 'always'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
