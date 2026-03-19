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
        title="Entra nel motore da un percorso più corto"
        lead="Lascia la tua email e ti portiamo direttamente nel profilo guidato: prima scegli se sei una persona fisica o un'attivita, poi le domande davvero rilevanti per te — poche, mirate, senza questionari infiniti."
        submitLabel="Invia link e continua"
        redirectTo="/onboarding?entry=apex"
      />
      <div className="stack">
        <div className="panel stack">
          <p className="eyebrow">Cosa succede dopo</p>
          <h2 style={{ fontSize: '2.2rem' }}>Non entri in un questionario infinito.</h2>
          <div className="stack subtle">
            <p>Prima ti chiediamo se stai cercando benefici personali o misure per la tua attivita. Le domande che seguono cambiano in base alla risposta.</p>
            <p>Dopo il primo salvataggio, il motore ricalcola subito e ti mostra match, status e campi mancanti con evidenze esplicite.</p>
          </div>
        </div>
        <div className="grid cards-3 entry-track">
          <article className="card stack entry-track-card">
            <span className="marketing-step-index">Chi sei</span>
            <h3>Persona o impresa?</h3>
            <p className="subtle">La prima scelta separa i benefici personali (INPS, detrazioni, bonus) dagli incentivi per attivita (crediti, voucher, misure imprenditoriali).</p>
          </article>
          <article className="card stack entry-track-card">
            <span className="marketing-step-index">Fatti stabili</span>
            <h3>Le domande che contano</h3>
            <p className="subtle">Per le persone: ISEE, composizione familiare, occupazione. Per le imprese: forma giuridica, regione, settore, dimensione.</p>
          </article>
          <article className="card stack entry-track-card">
            <span className="marketing-step-index">Profondita condizionale</span>
            <h3>Solo se serve davvero</h3>
            <p className="subtle">Dati su assunzioni, export, figli under 3 o condizioni specifiche compaiono solo per le famiglie di misure che li richiedono.</p>
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
