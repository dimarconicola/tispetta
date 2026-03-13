import { redirect } from 'next/navigation';

import { AdminConsoleNav } from '@/components/admin-console-nav';
import { getAdminMeasureFamilies, getSessionUser } from '@/lib/server-api';
import { formatDate } from '@/lib/utils';

export default async function AdminMeasureFamiliesPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');

  const families = await getAdminMeasureFamilies().catch(() => []);

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Admin</p>
        <h1 style={{ fontSize: '3rem' }}>Famiglie di misura</h1>
        <p className="subtle">
          Base canonica tra regime legale, documentazione operativa e superficie opportunita realmente azionabile.
        </p>
        <AdminConsoleNav />
      </section>
      <div className="grid cards-2">
        {families.map((family) => (
          <article className="card stack" key={family.id}>
            <div>
              <p className="eyebrow">{family.source_domain}</p>
              <h2 style={{ fontSize: '1.8rem' }}>{family.title}</h2>
            </div>
            <p className="subtle">
              Operatore: {family.operator_name}. Stato: {family.current_lifecycle_status}. Geografia: {family.geography}.
            </p>
            <div className="meta-list">
              <span>Slug: {family.slug}</span>
              <span>Actionable: {family.is_actionable ? 'si' : 'no'}</span>
              <span>Solo regime: {family.is_regime_only ? 'si' : 'no'}</span>
              <span>Documenti linkati: {family.documents_count}</span>
              <span>Requisiti strutturati: {family.requirements_count}</span>
              <span>Base legale primaria: {family.primary_legal_basis_count}</span>
              <span>Doc operativi primari: {family.primary_operational_count}</span>
              <span>Ultima verifica: {formatDate(family.verification_timestamp)}</span>
            </div>
            {family.legal_basis_references.length ? (
              <div className="stack">
                <strong>Riferimenti normativi</strong>
                <ul className="list-reset stack">
                  {family.legal_basis_references.slice(0, 3).map((reference) => (
                    <li key={reference}>
                      <a href={reference} target="_blank" rel="noreferrer">
                        {reference}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </div>
  );
}
