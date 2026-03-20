'use client';

import type { FormEvent } from 'react';
import { ArrowRight, Mail, Sparkles } from 'lucide-react';
import { useState, useTransition } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

const API_URL = '/api/proxy';

type MagicLinkFormProps = {
  eyebrow?: string;
  title?: string;
  lead?: string;
  submitLabel?: string;
  redirectTo?: string | null;
  initialEmail?: string;
};

export function MagicLinkForm({
  eyebrow = 'Accesso magic link',
  title = 'Accedi senza password',
  lead,
  submitLabel = 'Invia magic link',
  redirectTo,
  initialEmail,
}: MagicLinkFormProps) {
  const isLocalEnvironment = process.env.NODE_ENV !== 'production';
  const [email, setEmail] = useState(initialEmail ?? (isLocalEnvironment ? 'demo@example.com' : ''));
  const [message, setMessage] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const resolvedLead =
    lead ??
    `Inserisci la tua email. ${
      isLocalEnvironment ? 'Se disponibile, vedrai anche un link di anteprima locale.' : 'Riceverai un link di accesso valido per 30 minuti.'
    }`;

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    startTransition(async () => {
      setMessage(null);
      setPreviewUrl(null);
      try {
        const response = await fetch(`${API_URL}/v1/auth/request-magic-link`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, redirect_to: redirectTo ?? undefined }),
        });
        const data = (await response.json()) as { detail?: string; message?: string; preview_url?: string | null };
        if (!response.ok) {
          setMessage(data.detail ?? 'Impossibile inviare il magic link in questo momento.');
          return;
        }
        setMessage(data.message ?? 'Link inviato');
        setPreviewUrl(data.preview_url ?? null);
      } catch {
        setMessage('Connessione non riuscita. Riprova tra qualche secondo.');
      }
    });
  }

  return (
    <Card className="overflow-hidden border-slate-200 bg-white/92 shadow-[0_24px_70px_rgba(15,23,42,0.08)]">
      <CardHeader className="gap-4">
        <Badge variant="soft" className="w-fit">
          <Sparkles className="mr-1 size-3.5" />
          {eyebrow}
        </Badge>
        <div className="space-y-3">
          <CardTitle className="text-4xl leading-[0.95] text-slate-950">{title}</CardTitle>
          <CardDescription className="max-w-xl text-base leading-7 text-slate-500">{resolvedLead}</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <form className="grid gap-5" onSubmit={onSubmit}>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-slate-900">Email</span>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
              <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required className="pl-11" />
            </div>
          </label>
          <div className="flex flex-wrap gap-3">
            <Button type="submit" className="min-w-[13rem]" disabled={isPending}>
              {isPending ? 'Invio in corso...' : submitLabel}
              <ArrowRight className="size-4" />
            </Button>
            {previewUrl ? (
              <Button asChild variant="secondary">
                <a href={previewUrl}>Apri link di anteprima</a>
              </Button>
            ) : null}
          </div>
          {redirectTo ? (
            <div className="rounded-[1.4rem] border border-blue-100 bg-blue-50/80 px-4 py-3 text-sm leading-6 text-blue-950">
              Dopo il click entri direttamente nel percorso guidato, senza passare dalla schermata di accesso generica.
            </div>
          ) : null}
          {message ? <div className="banner">{message}</div> : null}
        </form>
      </CardContent>
    </Card>
  );
}
