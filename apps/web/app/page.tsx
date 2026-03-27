import Link from 'next/link';
import { headers } from 'next/headers';
import type { Metadata } from 'next';
import type { Route } from 'next';

import { ApexLanding } from '@/components/apex-landing';
import { FilterChips } from '@/components/filter-chips';
import { OpportunityCard } from '@/components/opportunity-card';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { APP_HOST, isApexLikeHost } from '@/lib/hosts';
import { getOpportunities, getProfileOverview, getSessionUser } from '@/lib/server-api';

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
    title: 'I tuoi match | Tispetta',
    alternates: { canonical: 'https://app.tispetta.eu/' },
  };
}

type HomeOpportunity = Awaited<ReturnType<typeof getOpportunities>>[number];

const SCOPE_ITEMS = [
  { label: 'Personale', value: 'personal' },
  { label: 'Attivita', value: 'business' },
];

function ProductHomePage({
  overview,
  opportunities,
  scope,
}: {
  overview: Awaited<ReturnType<typeof getProfileOverview>>;
  opportunities: HomeOpportunity[];
  scope: string;
}) {
  const confirmed = opportunities.filter((item) => item.match_status === 'confirmed');
  const likely = opportunities.filter((item) => item.match_status === 'likely');
  const unclear = opportunities.filter((item) => item.match_status === 'unclear');

  return (
    <div className="grid gap-8 pb-10">
      <section className="grid gap-6">
        <div className="max-w-3xl space-y-4">
          <Badge variant="soft" className="w-fit">I tuoi match</Badge>
          <h1 className="font-heading text-5xl font-semibold tracking-tight text-slate-950 sm:text-7xl">
            Le opportunita che emergono davvero dal tuo profilo <span className="text-gradient">adesso.</span>
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-slate-500">
            Qui vedi solo il feed personalizzato. Il catalogo generale resta in Cerca. Il profilo serve a rendere piu solidi i match che oggi sono ancora aperti.
          </p>
        </div>
        <div className="grid gap-3">
          <FilterChips items={SCOPE_ITEMS} active={scope || null} buildHref={(value) => `/${value ? `?scope=${encodeURIComponent(value)}` : ''}`} />
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.85fr)]">
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="outline" className="w-fit">Stato profilo</Badge>
            <CardTitle className="text-4xl leading-[0.95]">{overview?.summary.readiness_label ?? 'Profilo in aggiornamento'}</CardTitle>
            <CardDescription className="max-w-2xl text-base leading-7">
              {overview
                ? `Hai ${overview.summary.total_match_count} match personalizzati e ${overview.summary.clarifiable_match_count} schede ancora da chiarire.`
                : 'Stiamo riallineando il riepilogo del profilo.'}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-3">
            <Metric value={String(confirmed.length)} label="confermate" />
            <Metric value={String(likely.length)} label="compatibili" />
            <Metric value={String(unclear.length)} label="da chiarire" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="gap-3">
            <Badge variant="soft" className="w-fit">Orientamento</Badge>
            <CardTitle className="text-3xl">Profilo e catalogo non sono la stessa cosa.</CardTitle>
            <CardDescription className="text-base leading-7">
              Profilo = i tuoi dati. I tuoi match = il feed personalizzato. Cerca = il catalogo generale da esplorare senza mescolare i due livelli.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            <Link href={'/profile' as Route} className="button">
              Apri il profilo
            </Link>
            <Link href="/search" className="button-secondary">
              Apri il catalogo generale
            </Link>
          </CardContent>
        </Card>
      </section>

      <MatchSection
        eyebrow="Confermate"
        title="Le schede gia coerenti con i tuoi dati attuali"
        body="Sono le opportunita piu solide con il profilo di oggi."
        items={confirmed}
        empty="Nessuna scheda confermata al momento."
      />
      <MatchSection
        eyebrow="Compatibili"
        title="Quelle con buon fit, ma ancora da rifinire"
        body="Hanno un buon perimetro gia adesso, ma puoi renderle piu affidabili con poche informazioni in piu."
        items={likely}
        empty="Nessuna scheda compatibile da seguire adesso."
      />
      <MatchSection
        eyebrow="Da chiarire"
        title="Dove il profilo puo ancora cambiare il risultato"
        body="Qui trovi solo le schede che hanno bisogno di un passaggio in piu dal tuo profilo."
        items={unclear}
        empty="Nessun match aperto da chiarire in questo momento."
      />
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
            <OpportunityCard key={opportunity.id} opportunity={opportunity} profileReturnTo="/" showSaveToggle={false} />
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

function MatchSection({
  eyebrow,
  title,
  body,
  items,
  empty,
}: {
  eyebrow: string;
  title: string;
  body: string;
  items: HomeOpportunity[];
  empty: string;
}) {
  return (
    <section className="grid gap-5">
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2 className="section-title">{title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{body}</p>
        </div>
        <span className="text-sm text-slate-500">{items.length}</span>
      </div>
      {items.length > 0 ? (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {items.map((opportunity) => (
            <OpportunityCard key={opportunity.id} opportunity={opportunity} profileReturnTo="/" />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-6 text-sm leading-7 text-slate-600">{empty}</CardContent>
        </Card>
      )}
    </section>
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

  const user = await getSessionUser().catch(() => null);
  const [overview, opportunities] = await Promise.all([
    user ? getProfileOverview().catch(() => null) : Promise.resolve(null),
    getOpportunities({
      scope: scope || undefined,
      personalized_only: user ? true : undefined,
    }).catch(() => []),
  ]);

  if (!user) {
    return <PublicProductHome opportunities={opportunities} />;
  }

  return <ProductHomePage overview={overview} opportunities={opportunities} scope={scope} />;
}
