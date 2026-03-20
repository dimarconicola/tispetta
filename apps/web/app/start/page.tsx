import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';

import { MagicLinkForm } from '@/components/magic-link-form';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
      <MagicLinkForm
        eyebrow="Ingresso guidato"
        title="Entra nel motore da un percorso piu corto"
        lead="Lascia la tua email e ti portiamo direttamente nel profilo guidato: prima scegli se sei una persona fisica o un'attivita, poi arrivano solo le domande che cambiano davvero il matching."
        submitLabel="Invia link e continua"
        redirectTo="/onboarding?entry=apex"
      />
      <div className="grid gap-4">
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="outline" className="w-fit">Cosa succede dopo</Badge>
            <CardTitle className="text-4xl leading-[0.95]">Non entri in un questionario infinito.</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm leading-7 text-slate-600">
            <p>Prima distingui benefici personali e familiari da misure per attivita, freelance, startup o PMI.</p>
            <p>Dopo il primo salvataggio il motore ricalcola subito e ti mostra match, stato e campi mancanti con evidenze esplicite.</p>
            <p>Le domande sensibili o progettuali compaiono solo se una famiglia di misure attiva dipende davvero da quelle risposte.</p>
          </CardContent>
        </Card>
        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-1">
          <MiniStep title="Chi sei" body="Persona fisica oppure attivita/impresa." />
          <MiniStep title="Fatti stabili" body="Solo il core che sposta l'ammissibilita iniziale." />
          <MiniStep title="Precisione" body="Chiudi solo le opportunita che valgono la pena." />
        </div>
        <Card>
          <CardContent className="flex flex-wrap items-center justify-between gap-3 py-6 text-sm text-slate-600">
            <span>Se vuoi vedere prima il catalogo pubblico, puoi esplorarlo senza passare dall&apos;ingresso guidato.</span>
            <Link href="/search" className="button-secondary">
              Apri il catalogo live
            </Link>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function MiniStep({ title, body }: { title: string; body: string }) {
  return (
    <Card>
      <CardHeader className="gap-2 pb-3">
        <Badge variant="soft" className="w-fit">Step</Badge>
        <CardTitle className="text-xl">{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm leading-6 text-slate-600">{body}</CardContent>
    </Card>
  );
}
