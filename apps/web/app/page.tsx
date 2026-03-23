import Link from 'next/link';
import { headers } from 'next/headers';
import type { Metadata } from 'next';

import { FilterChips } from '@/components/filter-chips';
import { OpportunityCard } from '@/components/opportunity-card';
import { SearchBar } from '@/components/search-bar';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { getOpportunities, getProfile, getSessionUser } from '@/lib/server-api';
import { APP_HOST, isApexLikeHost } from '@/lib/hosts';

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
        'Tispetta trasforma norme, decreti, pagine operative e FAQ istituzionali in una superficie leggibile per startup, freelance, famiglie e PMI.',
      alternates: { canonical: 'https://tispetta.eu/' },
      openGraph: {
        title: 'Tispetta | Incentivi italiani letti come un prodotto',
        description:
          'Una superficie chiara per capire incentivi, crediti, bonus e agevolazioni italiane senza perdersi tra fonti sparse.',
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

function MarketingLandingPage({ opportunities }: { opportunities: HomeOpportunity[] }) {
  const preview = opportunities.slice(0, 3);
  const appStartUrl = `https://${APP_HOST}/start`;
  const appSearchUrl = `https://${APP_HOST}/search`;

  return (
    <div className="grid gap-8 pb-10">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] xl:items-stretch">
        <div className="grid gap-6 rounded-[2.25rem] border border-slate-200 bg-white/88 p-8 shadow-[0_30px_80px_rgba(15,23,42,0.08)]">
          <Badge variant="soft" className="w-fit">Mercato reale, fonti ufficiali, lettura operativa</Badge>
          <div className="grid gap-4">
            <h1 className="font-heading text-5xl font-semibold tracking-tight text-slate-950 sm:text-7xl">
              Ogni bonus, detrazione e incentivo che ti riguarda. <span className="text-gradient">In un posto solo.</span>
            </h1>
            <p className="max-w-3xl text-lg leading-8 text-slate-500">
              Tispetta legge norme, decreti, circolari e pagine operative e le trasforma in opportunita strutturate, criteri espliciti e match spiegabili.
              Per privati, famiglie, freelance e PMI.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a href={appStartUrl} className="button">
              Inizia dal profilo guidato
            </a>
            <a href={appSearchUrl} className="button-secondary">
              Vedi il catalogo live
            </a>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <Metric value={String(opportunities.length || 42)} label="opportunita pubbliche strutturate" />
            <Metric value="<=8" label="domande core prima dei primi match" />
            <Metric value="8" label="domini istituzionali monitorati" />
          </div>
        </div>

        <Card id="metodo" className="overflow-hidden bg-slate-950 text-white shadow-[0_30px_80px_rgba(15,23,42,0.2)]">
          <CardHeader className="gap-3 pb-4">
            <Badge variant="soft" className="w-fit bg-white/10 text-white">Perche e diverso</Badge>
            <CardTitle className="text-4xl leading-[0.95] text-white">Non un motore di ricerca di bandi.</CardTitle>
            <CardDescription className="text-base leading-7 text-slate-300">
              Il punto non e trovare piu pagine. Il punto e capire prima cosa e vivo, cosa richiede stato societario, cosa dipende da un progetto e cosa resta ambiguo.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-slate-300">
            <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">Base legale, pagine operative, FAQ e criteri sono tenuti insieme nello stesso record.</div>
            <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">Il matching e deterministico, con campi mancanti espliciti e nessuna eleggibilita inventata.</div>
            <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">L&apos;ingresso nell&apos;app e guidato: prima il core, poi la precisione che serve davvero.</div>
          </CardContent>
        </Card>
      </section>

      <section id="accesso" className="grid gap-5 rounded-[2rem] border border-slate-200 bg-white/88 p-6 shadow-sm lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="grid gap-4">
          <Badge variant="outline" className="w-fit">Ingresso</Badge>
          <h2 className="font-heading text-4xl font-semibold tracking-tight text-slate-950">Dal sito entri in un percorso guidato, non in un form generico.</h2>
          <p className="max-w-2xl text-base leading-7 text-slate-500">
            Parti sempre da te. Chiudi il profilo personale, vedi subito i primi match e aggiungi l attivita solo se esiste davvero.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <StepCard index="01" title="Email e sessione" body="Niente password: il link ti riporta direttamente nel flusso giusto." />
          <StepCard index="02" title="Profilo personale prima" body="Lavoro, fascia di eta, regione e nucleo fanno partire il feed subito con una base leggibile." />
          <StepCard index="03" title="Attivita solo se c e" body="Partita IVA, startup o PMI entrano dopo, nello stesso profilo e nello stesso feed." />
        </div>
      </section>

      <section id="per-chi" className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <AudienceCard eyebrow="Dipendente e Famiglia" title="Per chi ha diritti ma non li conosce" body="Assegno Unico, bonus nido, detrazioni figli, NASpI, casa e altri benefici personali." />
        <AudienceCard eyebrow="Founder" title="Per chi apre o struttura una startup" body="Stato innovativo, finestra di costituzione, Invitalia, crediti e percorsi di crescita." />
        <AudienceCard eyebrow="Freelance" title="Per chi lavora in proprio" body="Partita IVA, autoimpiego, agevolazioni leggere, bonus mirati e misure che non richiedono una PMI strutturata." />
        <AudienceCard eyebrow="PMI" title="Per chi gestisce una macchina operativa" body="Assunzioni, export, crediti d'imposta e investimenti digitali o energetici con vincoli espliciti." />
      </section>

      <section id="copertura" className="grid gap-5">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="eyebrow">Preview live</p>
            <h2 className="section-title">Tre schede tratte dal catalogo attuale</h2>
          </div>
          <a href={appSearchUrl} className="button-secondary">
            Esplora tutto il catalogo
          </a>
        </div>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {preview.map((opportunity) => (
            <OpportunityCard
              key={opportunity.id}
              opportunity={opportunity}
              detailHref={`https://${APP_HOST}/opportunities/${opportunity.slug}`}
              showSaveToggle={false}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

function ProductHomePage({
  profile,
  opportunities,
  scope,
}: {
  profile: Awaited<ReturnType<typeof getProfile>>;
  opportunities: HomeOpportunity[];
  scope: string;
}) {
  const topMatches = opportunities.slice(0, 6);
  const confirmed = opportunities.filter((item) => item.match_status === 'confirmed').slice(0, 3);
  const likely = opportunities.filter((item) => item.match_status === 'likely').slice(0, 3);

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
          {topMatches.map((opportunity) => (
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
          {opportunities.slice(0, 6).map((opportunity) => (
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

function StepCard({ index, title, body }: { index: string; title: string; body: string }) {
  return (
    <Card>
      <CardHeader className="gap-2 pb-3">
        <Badge variant="outline" className="w-fit">{index}</Badge>
        <CardTitle className="text-xl">{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm leading-6 text-slate-600">{body}</CardContent>
    </Card>
  );
}

function AudienceCard({ eyebrow, title, body }: { eyebrow: string; title: string; body: string }) {
  return (
    <Card>
      <CardHeader className="gap-2 pb-3">
        <Badge variant="outline" className="w-fit">{eyebrow}</Badge>
        <CardTitle className="text-2xl">{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm leading-6 text-slate-600">{body}</CardContent>
    </Card>
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
  const opportunities = await getOpportunities({ scope: scope || undefined }).catch(() => []);

  if (marketingHost) {
    return <MarketingLandingPage opportunities={opportunities} />;
  }

  const [user, profile] = await Promise.all([getSessionUser().catch(() => null), getProfile().catch(() => null)]);

  if (!user) {
    return <PublicProductHome opportunities={opportunities} />;
  }

  return <ProductHomePage profile={profile} opportunities={opportunities} scope={scope} />;
}
