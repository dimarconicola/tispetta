import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import type { ReactNode } from 'react';
import { AlertCircle, ArrowUpRight, CalendarDays, Euro, FileText, ShieldCheck } from 'lucide-react';

import { SaveToggle } from '@/components/save-toggle';
import { StatusPill } from '@/components/status-pill';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PUBLIC_APP_URL } from '@/lib/env';
import { getOpportunityDetail } from '@/lib/server-api';
import { categoryLabel, formatCurrency, formatDate } from '@/lib/utils';

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const opportunity = await getOpportunityDetail(slug).catch(() => null);

  if (!opportunity) {
    return {
      title: 'Opportunita non trovata',
      robots: { index: false, follow: false },
    };
  }

  const description = opportunity.short_description;
  const canonical = `${PUBLIC_APP_URL}/opportunities/${opportunity.slug}`;

  return {
    title: opportunity.title,
    description,
    alternates: { canonical },
    openGraph: { title: opportunity.title, description, url: canonical },
    twitter: { title: opportunity.title, description },
  };
}

export default async function OpportunityDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const opportunity = await getOpportunityDetail(slug).catch(() => null);
  if (!opportunity) {
    notFound();
  }

  const breakdown = opportunity.match_breakdown;

  return (
    <div className="grid gap-8 pb-8">
      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(340px,0.8fr)]">
        <Card>
          <CardHeader className="gap-4 pb-4">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="grid gap-3">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="soft" className="w-fit">{categoryLabel(opportunity.category)}</Badge>
                  <Badge variant="outline" className="w-fit">{scopeLabel(opportunity.opportunity_scope)}</Badge>
                </div>
                <CardTitle className="text-5xl leading-[0.95] text-slate-950 sm:text-6xl">{opportunity.title}</CardTitle>
                <p className="max-w-3xl text-base leading-8 text-slate-500">{opportunity.long_description ?? opportunity.short_description}</p>
              </div>
              <StatusPill status={opportunity.match_status} />
            </div>
          </CardHeader>
          <CardContent className="grid gap-5">
            <div className="grid gap-3 rounded-[1.75rem] border border-border/70 bg-slate-50/85 p-5 md:grid-cols-2">
              <DetailMeta icon={<Euro className="size-4 text-slate-400" />} label="Valore stimato" value={formatCurrency(opportunity.estimated_value_max)} />
              <DetailMeta icon={<CalendarDays className="size-4 text-slate-400" />} label="Scadenza" value={formatDate(opportunity.deadline_date)} />
              <DetailMeta icon={<ShieldCheck className="size-4 text-slate-400" />} label="Issuer" value={opportunity.issuer_name} />
              <DetailMeta icon={<FileText className="size-4 text-slate-400" />} label="Ultimo controllo" value={formatDate(opportunity.last_checked_at)} />
            </div>

            <div className="flex flex-wrap gap-3">
              <SaveToggle opportunityId={opportunity.id} initialSaved={opportunity.is_saved} />
              <Link className="button-secondary" href="/search">
                Torna alla ricerca
              </Link>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-5">
          <Card>
            <CardHeader className="gap-3 pb-4">
              <Badge variant="outline" className="w-fit">Match</Badge>
              <CardTitle className="text-3xl">Perche emerge adesso</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 text-sm text-slate-600">
              {opportunity.why_now ? <div className="rounded-[1.4rem] border border-blue-100 bg-blue-50/80 px-4 py-3 text-blue-950">{opportunity.why_now}</div> : null}
              {breakdown.matched_reasons.length > 0 ? (
                <div className="grid gap-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Why matched</span>
                  {breakdown.matched_reasons.map((reason) => (
                    <p key={reason} className="rounded-[1.25rem] border border-border/70 bg-white px-4 py-3">{reason}</p>
                  ))}
                </div>
              ) : (
                <p>Accedi e completa il profilo per vedere il ragionamento completo.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="gap-3 pb-4">
              <Badge variant="soft" className="w-fit">Cosa blocca la conferma</Badge>
              <CardTitle className="text-3xl">Che cosa ti manca per confermarla</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 text-sm text-slate-600">
              {breakdown.status === 'not_eligible' ? (
                <div className="flex gap-3 rounded-[1.4rem] border border-rose-200/80 bg-rose-50/80 px-4 py-3 text-rose-900">
                  <AlertCircle className="mt-0.5 size-4 shrink-0" />
                  <div className="grid gap-1">
                    <p className="font-semibold">Con i dati attuali questa scheda resta fuori profilo.</p>
                    <p className="leading-6 text-rose-900/80">Puoi comunque leggerla e tenerla salvata, ma oggi non emerge come coerente con il tuo profilo.</p>
                  </div>
                </div>
              ) : null}
              {breakdown.blocking_missing_facts.length > 0 ? (
                breakdown.blocking_missing_facts.map((fact) => (
                  <div key={fact.key} className="rounded-[1.4rem] border border-amber-200/70 bg-amber-50/70 px-4 py-3">
                    <p className="font-semibold text-amber-900">{fact.label}</p>
                    <p className="mt-1 leading-6 text-amber-900/80">{fact.why_this_question_matters_now ?? 'Questa risposta puo cambiare lo stato del match.'}</p>
                  </div>
                ))
              ) : (
                <p>Nessun blocco esplicito rilevato con i dati attuali.</p>
              )}
              <div className="flex flex-wrap gap-3">
                <Link href="/onboarding" className="button-secondary">
                  Completa il profilo
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader className="gap-3 pb-4">
            <Badge variant="outline" className="w-fit">Passi successivi</Badge>
            <CardTitle className="text-3xl">Cosa fare adesso</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-slate-600">
            {opportunity.next_steps.map((item) => (
              <div key={item} className="rounded-[1.25rem] border border-border/70 bg-white px-4 py-3">{item}</div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="gap-3 pb-4">
            <Badge variant="outline" className="w-fit">Documenti</Badge>
            <CardTitle className="text-3xl">Documenti richiesti</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-slate-600">
            {(opportunity.required_documents ?? ['Da verificare sul portale ufficiale']).map((item) => (
              <div key={item} className="rounded-[1.25rem] border border-border/70 bg-white px-4 py-3">{item}</div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader className="gap-3 pb-4">
            <Badge variant="soft" className="w-fit">Evidenze</Badge>
            <CardTitle className="text-3xl">Estratti usati per la scheda</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-slate-600">
            {opportunity.evidence_snippets.map((snippet) => (
              <div key={`${snippet.source}-${snippet.field}`} className="rounded-[1.4rem] border border-border/70 bg-white px-4 py-3">
                <p className="font-semibold text-slate-900">{snippet.field}</p>
                <p className="mt-1 leading-6">{snippet.quote}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="gap-3 pb-4">
            <Badge variant="soft" className="w-fit">Fonti ufficiali</Badge>
            <CardTitle className="text-3xl">Apri le fonti ufficiali</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-slate-600">
            {opportunity.official_links.map((link) => (
              <a
                key={link}
                href={link}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-between gap-3 rounded-[1.4rem] border border-border/70 bg-white px-4 py-3 transition-colors hover:border-primary/40 hover:text-primary"
              >
                <span className="truncate">{humanizeOfficialLink(link)}</span>
                <ArrowUpRight className="size-4 shrink-0" />
              </a>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function DetailMeta({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-3 rounded-[1.3rem] border border-white/80 bg-white px-4 py-3 shadow-sm">
      <span className="mt-0.5">{icon}</span>
      <div className="grid gap-1">
        <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</span>
        <span className="text-sm font-medium text-slate-900">{value}</span>
      </div>
    </div>
  );
}

function scopeLabel(scope: 'personal' | 'business' | 'hybrid') {
  if (scope === 'personal') return 'Per persona';
  if (scope === 'business') return 'Per attivita';
  return 'Persona + attivita';
}

function humanizeOfficialLink(value: string) {
  try {
    const url = new URL(value);
    const host = url.hostname.replace(/^www\./, '');
    const path = url.pathname === '/' ? '' : url.pathname.replace(/\/$/, '');
    return path ? `${host}${path}` : host;
  } catch {
    return value;
  }
}
