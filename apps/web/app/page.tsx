import Link from 'next/link';
import { headers } from 'next/headers';
import type { Metadata } from 'next';

import { OpportunityCard } from '@/components/opportunity-card';
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
        'Tispetta trasforma norme, decreti, pagine operative e FAQ istituzionali in una superficie leggibile per startup, freelance e PMI.',
      alternates: {
        canonical: 'https://tispetta.eu/',
      },
      openGraph: {
        title: 'Tispetta | Incentivi italiani letti come un prodotto',
        description:
          'Una superficie chiara per capire incentivi, crediti e agevolazioni italiane senza perdersi tra fonti sparse.',
        url: 'https://tispetta.eu/',
      },
      twitter: {
        title: 'Tispetta | Incentivi italiani letti come un prodotto',
        description:
          'Norme e pagine operative trasformate in opportunita strutturate, spiegate e filtrabili.',
      },
    };
  }

  return {
    title: 'Tispetta',
    alternates: {
      canonical: 'https://app.tispetta.eu/',
    },
  };
}

type HomeOpportunity = Awaited<ReturnType<typeof getOpportunities>>[number];

const matchStatusLabels: Record<string, string> = {
  confirmed: 'Confermato',
  likely: 'Probabile',
  unclear: 'Da chiarire',
  not_eligible: 'Non idoneo',
};

function getMarketingMatchLabel(matchStatus: string | null) {
  if (!matchStatus) {
    return 'Da valutare';
  }

  return matchStatusLabels[matchStatus] ?? 'Da valutare';
}

function MarketingPreviewCard({ opportunity }: { opportunity: HomeOpportunity }) {
  return (
    <article className="card marketing-preview-card stack">
      <div className="stack" style={{ gap: '0.4rem' }}>
        <span className="eyebrow">{opportunity.category.replace(/_/g, ' ')}</span>
        <h3 className="balance-title">{opportunity.title}</h3>
      </div>
      <p className="subtle line-clamp-3">{opportunity.short_description}</p>
      <div className="meta-list">
        <span>Stato: {getMarketingMatchLabel(opportunity.match_status)}</span>
        <span>Perimetro: {opportunity.geography_scope}</span>
        <span>Fonte verificata: {new Date(opportunity.last_checked_at).toLocaleDateString('it-IT')}</span>
      </div>
      <Link href={`https://${APP_HOST}/opportunities/${opportunity.slug}`} className="button-secondary">
        Apri scheda completa
      </Link>
    </article>
  );
}

function MarketingLandingPage({ opportunities }: { opportunities: HomeOpportunity[] }) {
  const catalogCountLabel = opportunities.length ? `${opportunities.length}` : '42';
  const preview = opportunities.slice(0, 3);
  const appStartUrl = `https://${APP_HOST}/start`;

  return (
    <div className="stack marketing-shell">
      <section className="marketing-hero">
        <div className="marketing-hero-copy stack">
          <p className="eyebrow">Mercato reale, fonti ufficiali, lettura operativa</p>
          <h1>Ogni bonus, detrazione e incentivo che ti riguarda — in un posto solo.</h1>
          <p className="lead">
            Tispetta legge norme, decreti, circolari e pagine operative INPS e Agenzia delle Entrate e le trasforma in
            opportunita strutturate, criteri espliciti e match spiegabili. Per privati, famiglie, freelance e PMI.
          </p>
          <div className="actions">
            <a href={appStartUrl} className="button">
              Inizia dal profilo guidato
            </a>
            <Link href={`https://${APP_HOST}/search`} className="button-secondary">
              Vedi il catalogo live
            </Link>
          </div>
          <div className="marketing-proof-grid">
            <div className="marketing-proof-card">
              <strong>{catalogCountLabel}</strong>
              <span>opportunita pubbliche gia strutturate</span>
            </div>
            <div className="marketing-proof-card">
              <strong>&lt;=8</strong>
              <span>domande core prima di mostrare match seri</span>
            </div>
            <div className="marketing-proof-card">
              <strong>8</strong>
              <span>domini istituzionali monitorati nel bootstrap nazionale</span>
            </div>
          </div>
        </div>
        <div className="marketing-hero-rail">
          <div className="marketing-orbit" aria-hidden="true" />
          <div className="panel marketing-note stack">
            <p className="eyebrow">Posizionamento</p>
            <h2>Non un motore di ricerca di bandi. Un layer decisionale sopra le fonti.</h2>
            <p className="subtle">
              Il punto non e trovare piu pagine. Il punto e capire prima: cosa e vivo, cosa richiede stato societario,
              cosa dipende da un progetto, cosa e ancora ambiguo.
            </p>
          </div>
        </div>
      </section>

      <section className="panel marketing-entry" id="accesso">
        <div className="marketing-entry-copy stack">
          <p className="eyebrow">Ingresso</p>
          <h2 className="section-title">Dal sito entri in un percorso guidato, non in un form generico.</h2>
          <p className="lead">
            Il primo passaggio non prova a sapere tutto. Ti porta dentro con una sequenza corta: email, nucleo stabile del profilo, primo shortlist. Solo dopo si aprono i moduli che servono davvero.
          </p>
          <div className="actions">
            <a href={appStartUrl} className="button">
              Apri l&apos;ingresso guidato
            </a>
            <Link href={`https://${APP_HOST}/auth/sign-in`} className="button-secondary">
              Vai al login diretto
            </Link>
          </div>
        </div>
        <div className="grid cards-3 marketing-entry-grid">
          <article className="card stack marketing-entry-card">
            <span className="marketing-step-index">01</span>
            <h3>Email e sessione</h3>
            <p className="subtle">Niente password. Il link ti riporta nel flusso giusto senza ripartire da zero.</p>
          </article>
          <article className="card stack marketing-entry-card">
            <span className="marketing-step-index">02</span>
            <h3>8 dati stabili</h3>
            <p className="subtle">Forma, fase attivita, regione, dimensione, settore e regime innovativo prima delle domande specialistiche.</p>
          </article>
          <article className="card stack marketing-entry-card">
            <span className="marketing-step-index">03</span>
            <h3>Profondita condizionale</h3>
            <p className="subtle">Assunzioni, export e investimenti si aprono solo se una famiglia di misure dipende davvero da quei dati.</p>
          </article>
        </div>
      </section>

      <section className="marketing-band panel" id="metodo">
        <div>
          <p className="eyebrow">Metodo</p>
          <h2 className="section-title">Una pipeline progettata per ridurre rumore e falsi positivi.</h2>
        </div>
        <div className="grid cards-3 marketing-steps">
          <article className="card stack marketing-step-card">
            <span className="marketing-step-index">01</span>
            <h3>Base legale</h3>
            <p className="subtle">Normattiva, Gazzetta, decreti attuativi, circolari e documenti collegati salvati come evidenza.</p>
          </article>
          <article className="card stack marketing-step-card">
            <span className="marketing-step-index">02</span>
            <h3>Surface operativa</h3>
            <p className="subtle">Pagine ministeriali, operatori, FAQ e guide applicative classificate per ruolo e stato della misura.</p>
          </article>
          <article className="card stack marketing-step-card">
            <span className="marketing-step-index">03</span>
            <h3>Match spiegabile</h3>
            <p className="subtle">Regole deterministiche, campi mancanti espliciti, ranking leggibile e nessuna eleggibilita inventata.</p>
          </article>
        </div>
      </section>

      <section className="split marketing-split" id="copertura">
        <div className="panel stack marketing-editorial">
          <p className="eyebrow">Copertura</p>
          <h2>Privati, freelance e PMI nello stesso impianto, senza schiacciare tutto in un questionario generico.</h2>
          <p className="lead">
            Le misure italiane coprono assi diversi: ISEE e composizione familiare per i benefici personali, stato
            innovativo e intenti di investimento per le imprese. Il profilo viene costruito in moduli: poche domande
            stabili per il tuo tipo, poi i dati specifici solo quando cambiano davvero i risultati.
          </p>
          <div className="marketing-fact-strip">
            <span>stato societario</span>
            <span>regime innovativo</span>
            <span>dimensione</span>
            <span>settore</span>
            <span>assunzioni</span>
            <span>transizione 5.0</span>
            <span>export</span>
            <span>ISEE</span>
            <span>figli a carico</span>
            <span>regime forfettario</span>
          </div>
        </div>
        <div className="grid marketing-audience-grid" id="per-chi">
          <article className="card stack marketing-audience-card">
            <p className="eyebrow">Dipendente e Famiglia</p>
            <h3>Per chi ha diritti ma non li conosce</h3>
            <p className="subtle">Assegno Unico, bonus nido, ANF, detrazioni figli, NASpI, detrazione mutuo, bonus prima casa. Benefici INPS e fiscali che milioni di italiani lasciano sul tavolo.</p>
          </article>
          <article className="card stack marketing-audience-card">
            <p className="eyebrow">Founder</p>
            <h3>Per chi apre o struttura una startup</h3>
            <p className="subtle">Stato innovativo, finestra di costituzione, ammissibilita Invitalia, crediti e percorsi di crescita.</p>
          </article>
          <article className="card stack marketing-audience-card">
            <p className="eyebrow">Freelance</p>
            <h3>Per chi lavora in proprio</h3>
            <p className="subtle">Partita IVA, regime forfettario, autoimpiego, agevolazioni leggere, bonus mirati e misure che non richiedono una PMI strutturata.</p>
          </article>
          <article className="card stack marketing-audience-card">
            <p className="eyebrow">PMI</p>
            <h3>Per chi gestisce una macchina gia operativa</h3>
            <p className="subtle">Assunzioni, export, crediti d&apos;imposta, investimenti digitali ed efficienza energetica con vincoli espliciti.</p>
          </article>
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <div>
            <p className="eyebrow">Preview live</p>
            <h2 className="section-title">Tre schede tratte dal catalogo attuale</h2>
          </div>
          <Link href={`https://${APP_HOST}/search`} className="button-secondary">
            Esplora tutte le opportunita
          </Link>
        </div>
        <div className="grid cards-3">
          {preview.map((opportunity) => (
            <MarketingPreviewCard key={opportunity.id} opportunity={opportunity} />
          ))}
        </div>
      </section>

      <section className="panel marketing-cta">
        <div className="stack">
          <p className="eyebrow">Entrata nell&apos;app</p>
          <h2>Il dominio principale racconta il prodotto. L&apos;uso vero parte da `app.tispetta.eu/start`.</h2>
          <p className="subtle">
            L&apos;app resta separata, con login, profilo, notifiche e catalogo filtrabile. L&apos;ingresso guidato conserva il contesto del sito e ti manda al profilo senza passare da una schermata neutra.
          </p>
        </div>
        <div className="actions">
          <a href={appStartUrl} className="button">
            Inizia guidato
          </a>
          <Link href={`https://${APP_HOST}/onboarding`} className="button-secondary">
            Inizia dal profilo
          </Link>
        </div>
      </section>
    </div>
  );
}

function ProductHomePage({
  profile,
  opportunities,
}: {
  profile: Awaited<ReturnType<typeof getProfile>>;
  opportunities: HomeOpportunity[];
}) {
  const confirmed = opportunities.filter((item) => item.match_status === 'confirmed').slice(0, 3);
  const likely = opportunities.filter((item) => item.match_status === 'likely').slice(0, 3);
  const expiring = [...opportunities]
    .filter((item) => item.deadline_date)
    .sort((a, b) => new Date(a.deadline_date ?? '').getTime() - new Date(b.deadline_date ?? '').getTime())
    .slice(0, 3);

  return (
    <div className="stack">
      <section className="hero">
        <div className="panel stack">
          <div>
            <p className="eyebrow">Dashboard personale</p>
            <h1>Cosa potrebbe essere rilevante per te adesso.</h1>
          </div>
          <p className="lead">
            {profile?.user_type ? `Profilo ${profile.user_type} in ${profile.region ?? 'Italia'}.` : 'Completa il profilo per affinare i match.'}{' '}
            {profile ? `Completezza attuale: ${profile.profile_completeness_score.toFixed(0)}%.` : ''}
          </p>
          <div className="actions">
            <Link href="/onboarding" className="button">
              Aggiorna profilo
            </Link>
            <Link href="/saved" className="button-secondary">
              Vedi salvate
            </Link>
          </div>
        </div>
        <div className="panel stack">
          <p className="eyebrow">Priorita immediate</p>
          <div className="stack">
            <div>
              <strong>{confirmed.length}</strong>
              <p className="subtle">opportunita confermate con dati attuali</p>
            </div>
            <div>
              <strong>{likely.length}</strong>
              <p className="subtle">opportunita promettenti da rifinire</p>
            </div>
            <div>
              <strong>{expiring.length}</strong>
              <p className="subtle">scadenze in arrivo da verificare</p>
            </div>
          </div>
        </div>
      </section>

      {profile && profile.profile_completeness_score < 70 ? (
        <div className="banner" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
          <span>
            Profilo al {profile.profile_completeness_score.toFixed(0)}% — completa le domande mancanti per sbloccare piu match.
          </span>
          <Link href="/onboarding" className="button-secondary" style={{ whiteSpace: 'nowrap', flexShrink: 0 }}>
            Completa profilo
          </Link>
        </div>
      ) : null}

      <section className="section">
        <div className="section-header">
          <div>
            <p className="eyebrow">Top opportunita</p>
            <h2 className="section-title">Confermate per il tuo profilo</h2>
          </div>
          <Link href="/search?matched_status=confirmed" className="button-secondary">
            Vedi tutte
          </Link>
        </div>
        <div className="grid cards-3">
          {(confirmed.length ? confirmed : opportunities.slice(0, 3)).map((opportunity) => (
            <OpportunityCard key={opportunity.id} opportunity={opportunity} />
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <div>
            <p className="eyebrow">Da sbloccare</p>
            <h2 className="section-title">Probabili, ma con qualche dato mancante</h2>
          </div>
          <Link href="/search?matched_status=likely" className="button-secondary">
            Vedi tutte
          </Link>
        </div>
        <div className="grid cards-3">
          {(likely.length ? likely : opportunities.slice(3, 6)).map((opportunity) => (
            <OpportunityCard key={opportunity.id} opportunity={opportunity} />
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <div>
            <p className="eyebrow">Urgenza</p>
            <h2 className="section-title">Scadenze da tenere sotto controllo</h2>
          </div>
          <Link href="/search?sort=deadline" className="button-secondary">
            Vedi tutte
          </Link>
        </div>
        <div className="grid cards-3">
          {expiring.map((opportunity) => (
            <OpportunityCard key={opportunity.id} opportunity={opportunity} />
          ))}
        </div>
      </section>
    </div>
  );
}

export default async function HomePage() {
  const marketingHost = await isMarketingRequest();
  const opportunities = await getOpportunities().catch(() => []);

  if (marketingHost) {
    return <MarketingLandingPage opportunities={opportunities} />;
  }

  const [user, profile] = await Promise.all([
    getSessionUser().catch(() => null),
    getProfile().catch(() => null),
  ]);
  const catalogCountLabel = opportunities.length ? `${opportunities.length}` : '40+';

  if (!user) {
    return (
      <div className="stack">
        <section className="hero">
          <div className="panel stack">
            <div>
              <p className="eyebrow">Opportunity intelligence per l&apos;Italia produttiva</p>
              <h1>Scopri bandi, incentivi e crediti che ti possono riguardare.</h1>
            </div>
            <p className="lead">
              Tispetta trasforma fonti ufficiali in opportunita strutturate, spiegate e abbinate al tuo profilo.
              Niente ricerca dispersiva, niente linguaggio opaco, niente promesse non verificabili.
            </p>
            <div className="actions">
              <Link href="/auth/sign-in" className="button">
                Accedi con magic link
              </Link>
              <Link href="/search" className="button-secondary">
                Esplora il catalogo demo
              </Link>
            </div>
            <div className="grid metrics">
              <div className="metric">
                <strong>{catalogCountLabel}</strong>
                <span>opportunita pubbliche derivate da fonti ufficiali</span>
              </div>
              <div className="metric">
                <strong>4</strong>
                <span>stati di eleggibilita spiegati con evidenze</span>
              </div>
              <div className="metric">
                <strong>8</strong>
                <span>domini istituzionali monitorati per il bootstrap nazionale</span>
              </div>
            </div>
          </div>
          <div className="panel stack">
            <p className="eyebrow">Perche funziona</p>
            <h2 style={{ fontSize: '2.4rem' }}>Deterministico dove conta, AI solo dove il testo e disordinato.</h2>
            <div className="stack subtle">
              <p>Snapshot delle fonti, record versionati, regole testate e spiegazioni leggibili.</p>
              <p>Il primo onboarding sblocca risultati subito. I dati mancanti diventano richieste mirate, non un questionario infinito.</p>
              <p>Operatori e admin vedono differenze, review queue e test di regola nello stesso prodotto.</p>
            </div>
          </div>
        </section>
        <section className="section">
          <div className="section-header">
            <div>
              <p className="eyebrow">Catalogo dimostrativo</p>
              <h2 className="section-title">Opportunita gia strutturate</h2>
            </div>
            <Link href="/search" className="button-secondary">
              Vai alla ricerca
            </Link>
          </div>
          <div className="grid cards-3">
            {opportunities.slice(0, 6).map((opportunity) => (
              <OpportunityCard key={opportunity.id} opportunity={opportunity} />
            ))}
          </div>
        </section>
      </div>
    );
  }

  return <ProductHomePage profile={profile} opportunities={opportunities} />;
}
