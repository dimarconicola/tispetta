import type { Route } from 'next';
import Link from 'next/link';

import { FilterChips } from '@/components/filter-chips';
import { OpportunityCard } from '@/components/opportunity-card';
import { SearchBar } from '@/components/search-bar';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getOpportunities, getSessionUser, searchOpportunities } from '@/lib/server-api';

const CATEGORY_ITEMS = [
  { label: 'Assunzioni', value: 'hiring_incentive' },
  { label: 'Digitale', value: 'digitization_incentive' },
  { label: 'Export', value: 'export_incentive' },
  { label: 'Sostenibilita', value: 'sustainability_incentive' },
  { label: 'Formazione', value: 'training_incentive' },
];

const STATUS_ITEMS = [
  { label: 'Confermate', value: 'confirmed' },
  { label: 'Compatibili', value: 'likely' },
  { label: 'Da chiarire', value: 'unclear' },
];

const SCOPE_ITEMS = [
  { label: 'Tutto', value: '' },
  { label: 'Personale', value: 'personal' },
  { label: 'Attivita', value: 'business' },
];

export default async function SearchPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  const query = typeof params.query === 'string' ? params.query : '';
  const category = typeof params.category === 'string' ? params.category : '';
  const matchedStatus = typeof params.matched_status === 'string' ? params.matched_status : '';
  const scope = typeof params.scope === 'string' ? params.scope : '';
  const sort = typeof params.sort === 'string' ? params.sort : '';
  const personalizedOnly = typeof params.personalized_only === 'string' ? params.personalized_only === 'true' : false;
  const user = await getSessionUser().catch(() => null);
  const currentSearch = new URLSearchParams();
  if (query) currentSearch.set('query', query);
  if (category) currentSearch.set('category', category);
  if (matchedStatus) currentSearch.set('matched_status', matchedStatus);
  if (scope) currentSearch.set('scope', scope);
  if (sort) currentSearch.set('sort', sort);
  if (personalizedOnly) currentSearch.set('personalized_only', 'true');
  const currentPath = `/search${currentSearch.toString() ? `?${currentSearch.toString()}` : ''}`;

  let opportunities = query
    ? personalizedOnly
      ? await getOpportunities({
          query,
          scope: scope || undefined,
          personalized_only: true,
        }).catch(() => [])
      : await searchOpportunities(query, scope || undefined).catch(() => [])
    : await getOpportunities({
        category,
        matched_status: matchedStatus || undefined,
        scope: scope || undefined,
        personalized_only: personalizedOnly || undefined,
      }).catch(() => []);

  if (category) {
    opportunities = opportunities.filter((item) => item.category === category);
  }
  if (matchedStatus) {
    opportunities = opportunities.filter((item) => item.match_status === matchedStatus);
  }
  if (scope) {
    opportunities = opportunities.filter((item) => scope === 'personal'
      ? item.opportunity_scope === 'personal' || item.opportunity_scope === 'hybrid'
      : item.opportunity_scope === 'business' || item.opportunity_scope === 'hybrid');
  }
  if (!matchedStatus) {
    opportunities = opportunities.filter((item) => item.match_status !== 'not_eligible');
  }
  if (sort === 'deadline') {
    opportunities = [...opportunities]
      .filter((item) => item.deadline_date)
      .sort((a, b) => new Date(a.deadline_date ?? '').getTime() - new Date(b.deadline_date ?? '').getTime());
  }

  const buildHref = (nextCategory: string | null) => {
    const search = new URLSearchParams();
    if (query) search.set('query', query);
    if (nextCategory) search.set('category', nextCategory);
    if (matchedStatus) search.set('matched_status', matchedStatus);
    if (scope) search.set('scope', scope);
    if (personalizedOnly) search.set('personalized_only', 'true');
    if (sort) search.set('sort', sort);
    return `/search${search.toString() ? `?${search.toString()}` : ''}`;
  };

  const buildStatusHref = (nextStatus: string | null) => {
    const search = new URLSearchParams();
    if (query) search.set('query', query);
    if (category) search.set('category', category);
    if (nextStatus) search.set('matched_status', nextStatus);
    if (scope) search.set('scope', scope);
    if (personalizedOnly) search.set('personalized_only', 'true');
    if (sort) search.set('sort', sort);
    return `/search${search.toString() ? `?${search.toString()}` : ''}`;
  };

  const buildScopeHref = (nextScope: string | null) => {
    const search = new URLSearchParams();
    if (query) search.set('query', query);
    if (category) search.set('category', category);
    if (matchedStatus) search.set('matched_status', matchedStatus);
    if (nextScope) search.set('scope', nextScope);
    if (personalizedOnly) search.set('personalized_only', 'true');
    if (sort) search.set('sort', sort);
    return `/search${search.toString() ? `?${search.toString()}` : ''}`;
  };

  const buildSortHref = () => {
    const search = new URLSearchParams();
    if (query) search.set('query', query);
    if (category) search.set('category', category);
    if (matchedStatus) search.set('matched_status', matchedStatus);
    if (scope) search.set('scope', scope);
    if (personalizedOnly) search.set('personalized_only', 'true');
    search.set('sort', 'deadline');
    return `/search?${search.toString()}`;
  };

  const buildPersonalizedHref = (enabled: boolean) => {
    const search = new URLSearchParams();
    if (query) search.set('query', query);
    if (category) search.set('category', category);
    if (matchedStatus) search.set('matched_status', matchedStatus);
    if (scope) search.set('scope', scope);
    if (sort) search.set('sort', sort);
    if (enabled) search.set('personalized_only', 'true');
    return `/search${search.toString() ? `?${search.toString()}` : ''}`;
  };

  return (
    <div className="grid gap-8 pb-8">
      <section className="grid gap-6">
        <div className="max-w-3xl space-y-4">
          <Badge variant="soft" className="w-fit">Catalogo live</Badge>
          <h1 className="font-heading text-5xl font-semibold tracking-tight text-slate-950 sm:text-7xl">
            Catalogo generale delle opportunita. <span className="text-gradient">Il tuo feed personalizzato sta altrove.</span>
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-slate-500">
            Cerca resta la superficie ampia: qui esplori tutto il catalogo. Se sei autenticato, puoi comunque limitarti ai risultati gia coerenti con il tuo profilo.
          </p>
        </div>

        <SearchBar defaultValue={query} />

        <div className="grid gap-4">
          <FilterChips items={SCOPE_ITEMS.filter((item) => item.value !== '')} active={scope || null} buildHref={buildScopeHref} />
          <FilterChips items={CATEGORY_ITEMS} active={category || null} buildHref={buildHref} />
          <FilterChips items={STATUS_ITEMS} active={matchedStatus || null} buildHref={buildStatusHref} />
          <div className="flex flex-wrap gap-3">
            {user ? (
              <Link
                href={buildPersonalizedHref(!personalizedOnly) as Route}
                className={`inline-flex min-h-11 items-center justify-center rounded-full border px-5 text-sm font-medium transition-all duration-200 ${
                  personalizedOnly
                    ? 'border-slate-900 bg-slate-900 text-white shadow-md shadow-slate-900/10'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                {personalizedOnly ? 'Stai vedendo solo i tuoi match' : 'Limita ai tuoi match'}
              </Link>
            ) : null}
            <Link
              href={buildSortHref() as Route}
              className={`inline-flex min-h-11 items-center justify-center rounded-full border px-5 text-sm font-medium transition-all duration-200 ${
                sort === 'deadline'
                  ? 'border-slate-900 bg-slate-900 text-white shadow-md shadow-slate-900/10'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              Ordina per scadenza
            </Link>
            {query || category || matchedStatus || sort || personalizedOnly ? (
              <Link href="/search" className="inline-flex min-h-11 items-center justify-center rounded-full border border-slate-200 bg-white px-5 text-sm font-medium text-slate-600 transition-all duration-200 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900">
                Resetta filtri
              </Link>
            ) : null}
          </div>
        </div>
      </section>

      <section className="grid gap-5">
        <div className="flex flex-col gap-3 border-b border-slate-200 pb-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="eyebrow">Risultati</p>
            <h2 className="font-heading text-2xl font-semibold text-slate-950 sm:text-3xl">{opportunities.length} opportunita trovate</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              {personalizedOnly
                ? 'Stai guardando solo le opportunita gia coerenti con il tuo profilo.'
                : 'Qui stai esplorando il catalogo generale, non il feed personalizzato.'}
            </p>
          </div>
          <Link href={'/' as Route} className="button-secondary w-fit">
            {user ? 'Vai ai tuoi match' : 'Torna alla home'}
          </Link>
        </div>

        {opportunities.length > 0 ? (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {opportunities.map((opportunity) => (
              <OpportunityCard key={opportunity.id} opportunity={opportunity} profileReturnTo={currentPath} />
            ))}
          </div>
        ) : (
          <Card>
            <CardHeader>
              <Badge variant="outline" className="w-fit">Nessun risultato</Badge>
              <CardTitle className="text-3xl">Nessuna opportunita trovata per i criteri selezionati.</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3 text-sm text-slate-600">
              <span>Prova a semplificare la query oppure rimuovi un filtro.</span>
              <Link href="/search" className="button-secondary">
                Cancella tutto
              </Link>
            </CardContent>
          </Card>
        )}
      </section>
    </div>
  );
}
