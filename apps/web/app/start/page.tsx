import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';

import { MagicLinkForm } from '@/components/magic-link-form';
import { getSessionUser } from '@/lib/server-api';

export const metadata: Metadata = {
  title: 'Ingresso guidato',
  description: 'Entra in Tispetta con un percorso guidato: email, profilo core, primo shortlist.',
  robots: {
    index: false,
    follow: false,
  },
};

export default async function StartPage() {
  const user = await getSessionUser().catch(() => null);
  if (user) {
    redirect('/onboarding?entry=apex');
  }

  return (
    <section className="split entry-shell">
      <MagicLinkForm
        eyebrow="Ingresso guidato"
        title="Entra nel motore da un percorso piu corto"
        lead="Lascia la tua email e ti portiamo direttamente nel profilo guidato: prima i fatti stabili che contano davvero, poi eventuali moduli specifici solo se servono a una misura reale."
        submitLabel="Invia link e continua"
        redirectTo="/onboarding?entry=apex"
      />
      <div className="stack">
        <div className="panel stack">
          <p className="eyebrow">Cosa succede dopo</p>
          <h2 style={{ fontSize: '2.2rem' }}>Non entri in un questionario infinito.</h2>
          <div className="stack subtle">
            <p>Il primo blocco resta entro 8 domande core: fase attivita, forma giuridica, regione, dimensione, settore e stato innovativo.</p>
            <p>Dopo il primo salvataggio, il motore ricalcola subito e ti mostra match, status e campi mancanti con evidenze esplicite.</p>
          </div>
        </div>
        <div className="grid cards-3 entry-track">
          <article className="card stack entry-track-card">
            <span className="marketing-step-index">Core entity</span>
            <h3>Fatti stabili</h3>
            <p className="subtle">Profilo tipo, fase attivita, legal form, regione, dimensione, settore.</p>
          </article>
          <article className="card stack entry-track-card">
            <span className="marketing-step-index">Strategic intent</span>
            <h3>Intenti che spostano la classifica</h3>
            <p className="subtle">Assunzioni, export, investimenti digitali o energetici solo quando incidono davvero.</p>
          </article>
          <article className="card stack entry-track-card">
            <span className="marketing-step-index">Conditional accuracy</span>
            <h3>Domande sensibili solo se necessarie</h3>
            <p className="subtle">Dati su target hire o condizioni personali compaiono solo per famiglie di misure che li richiedono.</p>
          </article>
        </div>
        <div className="panel stack">
          <p className="eyebrow">Alternativa</p>
          <div className="entry-inline-actions">
            <p className="subtle">Se vuoi vedere prima il catalogo pubblico, puoi esplorarlo senza passare dall&apos;ingresso guidato.</p>
            <Link href="/search" className="button-secondary">
              Apri il catalogo live
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
