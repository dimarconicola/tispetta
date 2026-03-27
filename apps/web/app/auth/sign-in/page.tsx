import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';

import { MagicLinkForm } from '@/components/magic-link-form';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getSessionUser } from '@/lib/server-api';

export const metadata: Metadata = {
  title: 'Accedi',
  description: 'Accedi a Tispetta con un magic link inviato alla tua email.',
  robots: {
    index: false,
    follow: false,
  },
};

export default async function SignInPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = searchParams ? await searchParams : {};
  const user = await getSessionUser().catch(() => null);
  if (user) {
    redirect('/');
  }

  const isLocalEnvironment = process.env.NODE_ENV !== 'production';
  const reason = Array.isArray(params.reason) ? params.reason[0] : params.reason;

  return (
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
      <div className="grid gap-4">
        {reason === 'session-expired' ? (
          <div className="banner">La sessione e scaduta. Ti inviamo un nuovo magic link per riprendere dal punto giusto.</div>
        ) : null}
        <MagicLinkForm />
      </div>
      <div className="grid gap-4">
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="outline" className="w-fit">Produzione</Badge>
            <CardTitle className="text-4xl leading-[0.95]">Il link arriva via email e scade in 30 minuti.</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm leading-7 text-slate-600">
            <p>Ogni accesso crea una sessione nuova sul dominio sicuro di Tispetta.</p>
            <p>Se non trovi il messaggio, controlla spam e promozioni prima di richiedere un secondo invio.</p>
            <p>
              Se arrivi dal sito principale e vuoi un percorso piu guidato, usa <Link href="/start" className="font-semibold text-primary">l&apos;ingresso dedicato</Link>.
            </p>
          </CardContent>
        </Card>

        {isLocalEnvironment ? (
          <Card>
            <CardHeader className="gap-3">
              <Badge variant="soft" className="w-fit">Locale</Badge>
              <CardTitle className="text-2xl">Account seed</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2 text-sm leading-6 text-slate-600">
              <span>`demo@example.com` per il percorso utente</span>
              <span>`admin@example.com` per il pannello operatore</span>
              <span>Mailpit: `http://localhost:8025` per controllare le email locali</span>
            </CardContent>
          </Card>
        ) : null}
      </div>
    </section>
  );
}
