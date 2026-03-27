import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';

import { MagicLinkForm } from '@/components/magic-link-form';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getSessionUser } from '@/lib/server-api';

export const metadata: Metadata = {
  title: 'Ingresso guidato',
  description: 'Entra in Tispetta con un percorso guidato: profilo personale, attivita opzionale, prime misure e approfondimenti utili.',
  robots: {
    index: false,
    follow: false,
  },
};

export default async function StartPage() {
  const user = await getSessionUser().catch(() => null);
  if (user) {
    redirect('/');
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
      <MagicLinkForm
        eyebrow="Ingresso guidato"
        title="Entra nel motore da un percorso piu corto"
        lead="Lascia la tua email e ti portiamo direttamente nel profilo guidato: partiamo da te, mostriamo i primi match e aggiungiamo l attivita solo se ti serve."
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
            <p>Prima chiudi il profilo personale che puo spostare subito bonus, lavoro, famiglia e parte dei match d impresa.</p>
            <p>Poi decidi se aggiungere anche un attivita. Se non ti serve, vai direttamente alle prime misure.</p>
            <p>Gli approfondimenti successivi compaiono uno alla volta e solo quando chiariscono davvero risultati live.</p>
          </CardContent>
        </Card>
        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-1">
          <MiniStep title="Profilo personale" body="Regione, lavoro, fascia di eta e nucleo: il minimo che serve per partire bene." />
          <MiniStep title="Attivita opzionale" body="Se hai una partita IVA o un impresa, la aggiungi nello stesso profilo." />
          <MiniStep title="Prime misure" body="Dopo il primo blocco vedi subito cosa emerge e decidi se affinare." />
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
