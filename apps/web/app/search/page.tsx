import Link from 'next/link';

import { OpportunityCard } from '@/components/opportunity-card';
import { getOpportunities, searchOpportunities } from '@/lib/server-api';

export default async function SearchPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  const query = typeof params.query === 'string' ? params.query : '';
  const category = typeof params.category === 'string' ? params.category : '';

  const opportunities = query ? await searchOpportunities(query).catch(() => []) : await getOpportunities({ category }).catch(() => []);

  return (
    <div className="stack">
      <section className="panel stack">
        <div>
          <p className="eyebrow">Ricerca</p>
          <h1 style={{ fontSize: '3rem' }}>Esplora opportunita e interpreta query in linguaggio naturale.</h1>
        </div>
        <form className="form-grid" action="/search">
          <label className="field" style={{ gridColumn: '1 / -1' }}>
            <span>Cosa stai cercando?</span>
            <input name="query" defaultValue={query} placeholder="Esempio: incentivi per assumere o bandi export per PMI" />
          </label>
          <label className="field">
            <span>Categoria</span>
            <select name="category" defaultValue={category}>
              <option value="">Tutte</option>
              <option value="digitization_incentive">Digitale</option>
              <option value="hiring_incentive">Assunzioni</option>
              <option value="export_incentive">Export</option>
              <option value="sustainability_incentive">Sostenibilita</option>
              <option value="training_incentive">Formazione</option>
            </select>
          </label>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button className="button" type="submit">
              Cerca
            </button>
          </div>
        </form>
      </section>

      <div className="section-header">
        <div>
          <p className="eyebrow">Risultati</p>
          <h2 className="section-title">{opportunities.length} opportunita trovate</h2>
        </div>
        <Link href="/" className="button-secondary">
          Torna alla dashboard
        </Link>
      </div>

      <div className="grid cards-3">
        {opportunities.map((opportunity) => (
          <OpportunityCard key={opportunity.id} opportunity={opportunity} />
        ))}
      </div>
    </div>
  );
}
