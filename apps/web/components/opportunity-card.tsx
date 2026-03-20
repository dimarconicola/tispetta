import Link from 'next/link';

import type { OpportunityCard as OpportunityCardType } from '@/lib/types';
import { categoryLabel, formatCurrency, formatDate } from '@/lib/utils';

import { SaveToggle } from './save-toggle';
import { StatusPill } from './status-pill';

export function OpportunityCard({ opportunity }: { opportunity: OpportunityCardType }) {
  return (
    <article className="card stack">
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.8rem', alignItems: 'flex-start' }}>
        <div className="stack" style={{ gap: '0.45rem' }}>
          <span className="eyebrow">{categoryLabel(opportunity.category)}</span>
          <h3 className="balance-title">{opportunity.title}</h3>
        </div>
        <StatusPill status={opportunity.match_status} />
      </div>
      <p className="subtle line-clamp-3">{opportunity.short_description}</p>
      <div className="meta-list">
        <span>Perimetro: {opportunity.geography_scope}</span>
        <span>Valore: {formatCurrency(opportunity.estimated_value_max)}</span>
        <span>Scadenza: {formatDate(opportunity.deadline_date)}</span>
      </div>
      {opportunity.user_visible_reasoning ? <div className="banner">{opportunity.user_visible_reasoning}</div> : null}
      {opportunity.missing_fields.length > 0 ? (
        <p className="subtle wrap-anywhere">Dati mancanti: {opportunity.missing_fields.join(', ')}</p>
      ) : null}
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.8rem', alignItems: 'center' }}>
        <Link className="button-secondary" href={`/opportunities/${opportunity.slug}`}>
          Apri dettaglio
        </Link>
        <SaveToggle opportunityId={opportunity.id} initialSaved={opportunity.is_saved} />
      </div>
    </article>
  );
}
