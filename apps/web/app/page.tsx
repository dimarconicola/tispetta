import Link from 'next/link';
import { headers } from 'next/headers';
import type { Metadata } from 'next';

import { ApexLanding } from '@/components/apex-landing';
import { FilterChips } from '@/components/filter-chips';
import { OpportunityCard } from '@/components/opportunity-card';
import { SearchBar } from '@/components/search-bar';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { APP_HOST, isApexLikeHost } from '@/lib/hosts';
import { getOpportunities, getProfile, getSessionUser } from '@/lib/server-api';

async function isMarketingRequest() {
  const headerStore = await headers();
  return isApexLikeHost(headerStore.get('host'));
}

export async function generateMetadata(): Promise<Metadata> {
  const marketingHost = await isMarketingRequest();

  if (marketingHost) {
    return {
      title: 'Tispetta | Incentivi italiani letti come un prodotto',
      description:
        'Tispetta legge norme, decreti e circolari e le trasforma in opportunita strutturate, criteri espliciti e match spiegabili.',
      alternates: { canonical: 'https://tispetta.eu/' },
      openGraph: {
        title: 'Tispetta | Incentivi italiani letti come un prodotto',
        description:
          'Una superficie chiara per capire incentivi, crediti e agevolazioni italiane senza perdersi tra fonti sparse.',
        url: 'https://tispetta.eu/',
      },
      twitter: {
        title: 'Tispetta | Incentivi italiani letti come un prodotto',
        description: 'Norme e pagine operative trasformate in opportunita strutturate, spiegate e filtrabili.',
      },
    };
  }

  return {
    title: 'Tispetta',
    alternates: { canonical: 'https://app.tispetta.eu/' },
  };
}

type HomeOpportunity = Awaited<ReturnType<typeof getOpportunities>>[number];

const CATEGORY_ITEMS = [
  { label: 'Assunzioni', value: 'hiring_incentive' },
  { label: 'Digitale', value: 'digitization_incentive' },
  { label: 'Export', value: 'export_incentive' },
  { label: 'Sostenibilita', value: 'sustainability_incentive' },
  { label: 'Formazione', value: 'training_incentive' },
];

const SCOPE_ITEMS = [
  { label: 'Personale', value: 'personal' },
  { label: 'Attivita', value: 'business' },
];

function ProductHomePage({
  profile,
  opportunities,
  scope,
}: {
  profile: Awaited<ReturnType<typeof getProfile>>;
  opportunities: HomeOpportunity[];
  scope: string;
}) {
  const visibleMatches = opportunities.filter((item) => item.match_status !== 'not_eligible');
  const confirmed = visibleMatches.filter((item) => item.match_status === 'confirmed').slice(0, 3);
  const likely = visibleMatches.filter((item) => item.match_status === 'likely').slice(0, 3);

  return (
    <div className="grid gap-8 pb-10">
      <section className="grid gap-6">
        <div className="max-w-3xl space-y-4">
          <Badge variant="soft" className="w-fit">Dashboard personale</Badge>
          <h1 className="font-heading text-5xl font-semibold tracking-tight text-slate-950 sm:text-7xl">
            Cosa potrebbe essere rilevante per te <span className="text-gradient">adesso.</span>
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-slate-500">
            {profile?.user_type && profile.user_type !== 'persona_fisica'
              ? `Profilo personale attivo con area principale ${profile.region ?? 'Italia'} e contesto ${profile.user_type}. `
              : `Profilo personale attivo${profile?.region ? ` in ${profile.region}` : ''}. `}
            Completezza attuale {Math.round(profile?.profile_completeness_score ?? 0)}%. Cerca, salva e chiarisci prima i match che possono salire di stato.
          </p>
        </div>
        <SearchBar defaultValue="" />
        <div className="grid gap-3">
          <FilterChips items={SCOPE_ITEMS} active={scope || null} buildHref={(value) => `/${value ? `?scope=${encodeURIComponent(value)}` : ''}`} />
          <FilterChips
            items={CATEGORY_ITEMS}
            active={null}
            buildHref={(value) => {
              const search = new URLSearchParams();
              if (value) search.set('category', value);
              if (scope) search.set('scope', scope);
              return `/search${search.toString() ? `?${search.toString()}` : ''}`;
            }}
          />
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.85fr)]">
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="outline" className="w-fit">Snapshot</Badge>
            <CardTitle className="text-4xl leading-[0.95]">Hai gia una base spendibile. Ora scegli dove chiudere i blocchi.</CardTitle>
            <CardDescription className="max-w-2xl text-base leading-7">
              I match sono gia ordinati per stato, urgenza e potenziale. Il profilo serve a rendere espliciti i campi che cambiano davvero il risultato.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-3">
            <Metric value={String(confirmed.length)} label="confermate ora" />
            <Metric value={String(likely.length)} label="probabili da chiudere" />
            <Metric value={`${Math.round(profile?.profile_completeness_score ?? 0)}%`} label="completezza attuale" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="gap-3">
            <Badge variant="soft" className="w-fit">Azione</Badge>
            <CardTitle className="text-3xl">Non serve completare tutto.</CardTitle>
            <CardDescription className="text-base leading-7">Completa prima le risposte che spostano stato e priorita. Il resto puo arrivare dopo.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            <Link href="/onboarding" className="button">
              Aggiorna il profilo
            </Link>
            <Link href="/saved" className="button-secondary">
              Apri salvate
            </Link>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-5">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="eyebrow">Top opportunita</p>
            <h2 className="section-title">Le prime sei che meritano attenzione</h2>
          </div>
          <Link href="/search" className="button-secondary">
            Vedi tutto
          </Link>
        </div>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {visibleMatches.slice(0, 6).map((opportunity) => (
            <OpportunityCard key={opportunity.id} opportunity={opportunity} />
          ))}
        </div>
      </section>
    </div>
  );
}

function PublicProductHome({ opportunities }: { opportunities: HomeOpportunity[] }) {
  return (
    <div className="grid gap-8 pb-10">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
        <div className="grid gap-6 rounded-[2.25rem] border border-slate-200 bg-white/88 p-8 shadow-[0_30px_80px_rgba(15,23,42,0.08)]">
          <Badge variant="soft" className="w-fit">Opportunity intelligence per l&apos;Italia produttiva</Badge>
          <div className="grid gap-4">
            <h1 className="font-heading text-5xl font-semibold tracking-tight text-slate-950 sm:text-7xl">
              Scopri bandi, incentivi e crediti che ti possono riguardare.
            </h1>
            <p className="max-w-3xl text-lg leading-8 text-slate-500">
              Tispetta trasforma fonti ufficiali in opportunita strutturate, spiegate e abbinate al tuo profilo. Niente ricerca dispersiva, niente linguaggio opaco.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/start" className="button">
              Accedi con ingresso guidato
            </Link>
            <Link href="/search" className="button-secondary">
              Esplora il catalogo demo
            </Link>
          </div>
        </div>
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="outline" className="w-fit">Metodo</Badge>
            <CardTitle className="text-4xl leading-[0.95]">Deterministico dove conta, AI solo dove il testo e sporco.</CardTitle>
            <CardDescription className="text-base leading-7">Snapshot delle fonti, record versionati, regole testate e spiegazioni leggibili.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-slate-600">
            <div className="rounded-[1.5rem] border border-border/70 bg-slate-50/80 p-4">Il primo onboarding sblocca risultati subito.</div>
            <div className="rounded-[1.5rem] border border-border/70 bg-slate-50/80 p-4">I dati mancanti diventano richieste mirate, non un questionario infinito.</div>
            <div className="rounded-[1.5rem] border border-border/70 bg-slate-50/80 p-4">Ogni opportunita resta collegata a fonti ufficiali e evidenze.</div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-5">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="eyebrow">Catalogo dimostrativo</p>
            <h2 className="section-title">Opportunita gia strutturate</h2>
          </div>
          <Link href="/search" className="button-secondary">
            Vai alla ricerca
          </Link>
        </div>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {opportunities.filter((opportunity) => opportunity.match_status !== 'not_eligible').slice(0, 6).map((opportunity) => (
            <OpportunityCard key={opportunity.id} opportunity={opportunity} showSaveToggle={false} />
          ))}
        </div>
      </section>
    </div>
  );
}

function Metric({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-[1.75rem] border border-slate-200 bg-slate-50/85 p-4 shadow-sm">
      <strong className="block font-heading text-3xl font-semibold text-slate-950">{value}</strong>
      <span className="mt-2 block text-sm leading-6 text-slate-500">{label}</span>
    </div>
  );
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const scope = typeof params.scope === 'string' ? params.scope : '';
  const marketingHost = await isMarketingRequest();

  if (marketingHost) {
    return <ApexLanding appBaseUrl={`https://${APP_HOST}`} />;
  }

  const opportunities = await getOpportunities({ scope: scope || undefined }).catch(() => []);
  const [user, profile] = await Promise.all([getSessionUser().catch(() => null), getProfile().catch(() => null)]);

  if (!user) {
    return <PublicProductHome opportunities={opportunities} />;
  }

  return <ProductHomePage profile={profile} opportunities={opportunities} scope={scope} />;
}
