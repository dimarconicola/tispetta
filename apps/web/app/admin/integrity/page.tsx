import { AdminConsoleNav } from '@/components/admin-console-nav';
import { getAdminIntegrity } from '@/lib/server-api';

export default async function AdminIntegrityPage() {
  const snapshot = await getAdminIntegrity().catch(() => null);

  return (
    <div className="stack">
      <AdminConsoleNav />
      <section className="panel stack">
        <div>
          <p className="eyebrow">Integrity</p>
          <h1 style={{ fontSize: '2.4rem' }}>Stato schema e duplicati critici.</h1>
          <p className="subtle">Controllo rapido per capire se il database e allineato all&apos;head Alembic e se esistono collisioni sui vincoli piu sensibili.</p>
        </div>
        {snapshot ? (
          <div className="grid cards-3">
            <article className="card stack">
              <span className="eyebrow">Schema</span>
              <strong style={{ fontSize: '1.8rem' }}>{snapshot.schema_current ? 'Allineato' : 'Fuori sync'}</strong>
              <p className="subtle">Current: {snapshot.current_revision ?? 'none'}</p>
              <p className="subtle">Head: {snapshot.head_revision}</p>
            </article>
            {snapshot.checks.map((check) => (
              <article className="card stack" key={check.name}>
                <span className="eyebrow">{check.name}</span>
                <strong style={{ fontSize: '1.8rem' }}>{check.duplicate_group_count}</strong>
                <p className="subtle">gruppi duplicati</p>
                <p className="subtle">righe coinvolte: {check.duplicate_row_count}</p>
                {check.sample_values.length ? (
                  <p className="subtle">esempi: {check.sample_values.join(', ')}</p>
                ) : (
                  <p className="subtle">nessun duplicato rilevato</p>
                )}
              </article>
            ))}
          </div>
        ) : (
          <div className="banner">Impossibile caricare lo snapshot di integrity.</div>
        )}
      </section>
    </div>
  );
}
