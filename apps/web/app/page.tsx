import Link from 'next/link';

import { OpportunityCard } from '@/components/opportunity-card';
import { getOpportunities, getProfile, getSessionUser } from '@/lib/server-api';

export default async function HomePage() {
  const [user, profile, opportunities] = await Promise.all([
    getSessionUser().catch(() => null),
    getProfile().catch(() => null),
    getOpportunities().catch(() => []),
  ]);

  const confirmed = opportunities.filter((item) => item.match_status === 'confirmed').slice(0, 3);
  const likely = opportunities.filter((item) => item.match_status === 'likely').slice(0, 3);
  const expiring = [...opportunities]
    .filter((item) => item.deadline_date)
    .sort((a, b) => new Date(a.deadline_date ?? '').getTime() - new Date(b.deadline_date ?? '').getTime())
    .slice(0, 3);

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
                <strong>25+</strong>
                <span>opportunita seed con regole e fixture</span>
              </div>
              <div className="metric">
                <strong>4</strong>
                <span>stati di eleggibilita spiegati con evidenze</span>
              </div>
              <div className="metric">
                <strong>1</strong>
                <span>catalogo focalizzato su freelance, startup e PMI</span>
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

      <section className="section">
        <div className="section-header">
          <div>
            <p className="eyebrow">Top opportunita</p>
            <h2 className="section-title">Confermate per il tuo profilo</h2>
          </div>
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
