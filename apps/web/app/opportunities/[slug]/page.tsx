import Link from 'next/link';
import { notFound } from 'next/navigation';

import { SaveToggle } from '@/components/save-toggle';
import { StatusPill } from '@/components/status-pill';
import { getOpportunityDetail } from '@/lib/server-api';
import { categoryLabel, formatCurrency, formatDate } from '@/lib/utils';

export default async function OpportunityDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const opportunity = await getOpportunityDetail(slug).catch(() => null);
  if (!opportunity) {
    notFound();
  }

  return (
    <div className="stack">
      <section className="split">
        <div className="panel stack">
          <div className="stack" style={{ gap: '0.5rem' }}>
            <p className="eyebrow">{categoryLabel(opportunity.category)}</p>
            <h1 style={{ fontSize: '3.6rem' }}>{opportunity.title}</h1>
            <StatusPill status={opportunity.match_status} />
          </div>
          <p className="lead">{opportunity.long_description ?? opportunity.short_description}</p>
          <div className="detail-list">
            <span>Issuer: {opportunity.issuer_name}</span>
            <span>Valore stimato: {formatCurrency(opportunity.estimated_value_max)}</span>
            <span>Scadenza: {formatDate(opportunity.deadline_date)}</span>
            <span>Ultimo controllo: {formatDate(opportunity.last_checked_at)}</span>
          </div>
          <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap' }}>
            <SaveToggle opportunityId={opportunity.id} initialSaved={opportunity.is_saved} />
            <Link className="button-secondary" href="/search">
              Torna alla ricerca
            </Link>
          </div>
        </div>
        <div className="panel stack">
          <p className="eyebrow">Perche corrisponde</p>
          <div className="stack subtle">
            {opportunity.why_this_matches.length ? (
              opportunity.why_this_matches.map((item) => <p key={item}>{item}</p>)
            ) : (
              <p>Accedi e completa il profilo per vedere il ragionamento completo.</p>
            )}
          </div>
          {opportunity.what_is_missing.length ? (
            <div className="banner">Mancano informazioni su: {opportunity.what_is_missing.join(', ')}</div>
          ) : null}
        </div>
      </section>

      <section className="grid cards-2">
        <article className="card stack">
          <h2>Passi successivi</h2>
          <ul className="list-reset stack">
            {opportunity.next_steps.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
        <article className="card stack">
          <h2>Documenti richiesti</h2>
          <ul className="list-reset stack">
            {(opportunity.required_documents ?? ['Da verificare sul portale ufficiale']).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="grid cards-2">
        <article className="card stack">
          <h2>Evidenze</h2>
          <ul className="list-reset stack">
            {opportunity.evidence_snippets.map((snippet) => (
              <li key={`${snippet.source}-${snippet.field}`}>
                <strong>{snippet.field}:</strong> {snippet.quote}
              </li>
            ))}
          </ul>
        </article>
        <article className="card stack">
          <h2>Fonti ufficiali</h2>
          <ul className="list-reset stack">
            {opportunity.official_links.map((link) => (
              <li key={link}>
                <a href={link} target="_blank" rel="noreferrer">
                  {link}
                </a>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </div>
  );
}
