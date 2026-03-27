import Link from 'next/link';
import { redirect } from 'next/navigation';
import type { ReactNode } from 'react';
import { AlertCircle, ArrowRight, BriefcaseBusiness, CheckCircle2, PencilLine, UserRound } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { buildProfileEditHref } from '@/lib/profile-ui';
import { getProfileOverview, getSessionUser } from '@/lib/server-api';
import type { ProfileOverviewSection } from '@/lib/types';

function SummaryPill({ label }: { label: string }) {
  return <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">{label}</span>;
}

export default async function ProfilePage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) {
    redirect('/auth/sign-in');
  }

  const overview = await getProfileOverview().catch(() => null);
  if (!overview) {
    return (
      <Card>
        <CardContent className="py-10 text-sm leading-7 text-slate-600">
          Non riusciamo a caricare il riepilogo del profilo in questo momento. Riprova tra un attimo.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-8 pb-10">
      <section className="grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.85fr)]">
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="soft" className="w-fit">Profilo</Badge>
            <CardTitle className="text-5xl leading-[0.95]">Le informazioni che definiscono i tuoi match.</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 text-base leading-7 text-slate-600">
            <p>
              Qui trovi solo il riepilogo del profilo: cosa e gia completo, cosa manca ancora e dove intervenire per chiarire i match che restano aperti.
            </p>
            <div className="flex flex-wrap gap-2">
              {overview.summary.completed_labels.map((label) => (
                <SummaryPill key={label} label={label} />
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="gap-3">
            <Badge variant="outline" className="w-fit">Stato profilo</Badge>
            <CardTitle className="text-3xl">{overview.summary.readiness_label}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-slate-600">
            <div className="rounded-[1.4rem] border border-slate-200 bg-slate-50/80 px-4 py-3">
              Completezza attuale {Math.round(overview.summary.profile_completeness_score)}%
            </div>
            <div className="rounded-[1.4rem] border border-slate-200 bg-slate-50/80 px-4 py-3">
              {overview.summary.total_match_count} match personalizzati, {overview.summary.clarifiable_match_count} ancora da chiarire
            </div>
            <div className="flex flex-wrap gap-3">
              <Link href="/" className="button">Vai ai tuoi match</Link>
              <Link href="/search" className="button-secondary">Apri il catalogo generale</Link>
            </div>
          </CardContent>
        </Card>
      </section>

      {overview.summary.missing_labels.length > 0 ? (
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="outline" className="w-fit">Da chiarire</Badge>
            <CardTitle className="text-3xl">Le prossime informazioni che possono ancora spostare il risultato.</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {overview.summary.missing_labels.map((label) => (
              <SummaryPill key={label} label={label} />
            ))}
          </CardContent>
        </Card>
      ) : null}

      <section className="grid gap-5 xl:grid-cols-2">
        <ProfileSectionCard
          icon={<UserRound className="size-5" />}
          section={overview.personal}
        />
        <ProfileSectionCard
          icon={<BriefcaseBusiness className="size-5" />}
          section={overview.business}
        />
      </section>
    </div>
  );
}

function ProfileSectionCard({
  icon,
  section,
}: {
  icon: ReactNode;
  section: ProfileOverviewSection;
}) {
  return (
    <Card>
      <CardHeader className="gap-3">
        <div className="flex items-center gap-3">
          <span className="flex size-12 items-center justify-center rounded-2xl bg-slate-50 text-slate-900">{icon}</span>
          <div className="grid gap-1">
            <Badge variant="soft" className="w-fit">{section.title}</Badge>
            <CardTitle className="text-3xl">{section.status_label}</CardTitle>
          </div>
        </div>
        <p className="max-w-2xl text-sm leading-7 text-slate-600">{section.description}</p>
      </CardHeader>
      <CardContent className="grid gap-5">
        <div className="rounded-[1.4rem] border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-600">
          {section.answered_count > 0
            ? `${section.answered_count} informazioni gia registrate.`
            : 'Nessun dato registrato in questo blocco.'}
        </div>

        {section.answered_fields.length > 0 ? (
          <div className="grid gap-3">
            {section.answered_fields.map((field) => (
              <div key={field.key} className="rounded-[1.35rem] border border-border/70 bg-white px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{field.label}</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{field.formatted_value}</p>
              </div>
            ))}
          </div>
        ) : null}

        {section.missing_labels.length > 0 ? (
          <div className="grid gap-3 rounded-[1.4rem] border border-amber-200 bg-amber-50/70 px-4 py-4">
            <div className="flex items-start gap-2 text-amber-900">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <div className="grid gap-2">
                <p className="text-sm font-semibold">Mancano ancora alcuni dati essenziali.</p>
                <div className="flex flex-wrap gap-2">
                  {section.missing_labels.map((label) => (
                    <SummaryPill key={label} label={label} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-start gap-2 rounded-[1.4rem] border border-emerald-200 bg-emerald-50/70 px-4 py-4 text-emerald-900">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            <p className="text-sm font-medium">Il minimo indispensabile di questo blocco e gia completo.</p>
          </div>
        )}

        <div className="flex flex-wrap gap-3">
          <Link
            href={buildProfileEditHref(section.edit_target, { returnTo: '/profile' })}
            className="button"
          >
            <PencilLine className="size-4" />
            {section.edit_target.label}
          </Link>
          <Link href="/" className="button-secondary">
            Vai ai tuoi match
            <ArrowRight className="size-4" />
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
