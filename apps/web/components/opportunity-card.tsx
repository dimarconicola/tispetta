import type { Route } from 'next';
import Link from 'next/link';
import { ArrowRight, CalendarDays, Euro, MapPin } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import type { OpportunityCard as OpportunityCardType } from '@/lib/types';
import { categoryLabel, cn, formatCurrency, formatDate } from '@/lib/utils';

import { SaveToggle } from './save-toggle';
import { StatusPill } from './status-pill';

const categoryTheme: Record<string, string> = {
  hiring_incentive: 'bg-emerald-50/90 border-emerald-100 hover:border-emerald-300 hover:shadow-emerald-500/10',
  freelance_incentive: 'bg-violet-50/90 border-violet-100 hover:border-violet-300 hover:shadow-violet-500/10',
  export_incentive: 'bg-sky-50/90 border-sky-100 hover:border-sky-300 hover:shadow-sky-500/10',
  digitization_incentive: 'bg-blue-50/90 border-blue-100 hover:border-blue-300 hover:shadow-blue-500/10',
  sustainability_incentive: 'bg-green-50/90 border-green-100 hover:border-green-300 hover:shadow-green-500/10',
  training_incentive: 'bg-orange-50/90 border-orange-100 hover:border-orange-300 hover:shadow-orange-500/10',
  innovation_incentive: 'bg-fuchsia-50/90 border-fuchsia-100 hover:border-fuchsia-300 hover:shadow-fuchsia-500/10',
  startup_incentive: 'bg-indigo-50/90 border-indigo-100 hover:border-indigo-300 hover:shadow-indigo-500/10',
  tax_benefit: 'bg-slate-100/95 border-slate-200 hover:border-slate-300 hover:shadow-slate-500/10',
};

export function OpportunityCard({
  opportunity,
  detailHref,
  showSaveToggle = true,
}: {
  opportunity: OpportunityCardType;
  detailHref?: string;
  showSaveToggle?: boolean;
}) {
  const theme = categoryTheme[opportunity.category] ?? 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-slate-500/10';
  const targetHref = detailHref ?? `/opportunities/${opportunity.slug}`;
  const isExternalHref = targetHref.startsWith('http://') || targetHref.startsWith('https://');

  return (
    <Card className={cn('group h-full overflow-hidden border shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl', theme)}>
      <CardHeader className="gap-4 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge variant="soft" className="w-fit bg-white/70 text-slate-700">
                {categoryLabel(opportunity.category)}
              </Badge>
              <Badge variant="outline" className="w-fit bg-white/55 text-slate-700">
                {scopeLabel(opportunity.opportunity_scope)}
              </Badge>
            </div>
            <CardTitle className="balance-title text-2xl leading-tight text-slate-950">{opportunity.title}</CardTitle>
          </div>
          <StatusPill status={opportunity.match_status} />
        </div>
        <p className="line-clamp-3 text-sm leading-6 text-slate-600">{opportunity.short_description}</p>
      </CardHeader>
      <CardContent className="grid gap-5 pt-0">
        <div className="grid gap-2 rounded-[1.5rem] border border-white/70 bg-white/65 p-4 text-sm text-slate-700 shadow-sm">
          <div className="flex items-center gap-2">
            <MapPin className="size-4 text-slate-400" />
            <span>{opportunity.geography_scope}</span>
          </div>
          <div className="flex items-center gap-2">
            <Euro className="size-4 text-slate-400" />
            <span>{formatCurrency(opportunity.estimated_value_max)}</span>
          </div>
          <div className="flex items-center gap-2">
            <CalendarDays className="size-4 text-slate-400" />
            <span>{formatDate(opportunity.deadline_date)}</span>
          </div>
        </div>

        {opportunity.match_reasons.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {opportunity.match_reasons.slice(0, 2).map((reason) => (
              <span key={reason} className="rounded-full border border-white/80 bg-white/75 px-3 py-1 text-xs font-medium text-slate-600">
                {reason}
              </span>
            ))}
          </div>
        ) : null}

        {opportunity.why_now ? (
          <div className="rounded-[1.4rem] border border-blue-100 bg-white/80 px-4 py-3 text-sm leading-6 text-slate-700">
            {opportunity.why_now}
          </div>
        ) : null}

        {opportunity.blocking_missing_labels.length > 0 ? (
          <div className="grid gap-2 rounded-[1.4rem] border border-amber-200/70 bg-amber-50/70 px-4 py-3 text-sm text-amber-900">
            <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-700">Da completare</span>
            <p className="m-0 wrap-anywhere">Ti manca ancora: {opportunity.blocking_missing_labels.slice(0, 2).join(', ')}.</p>
          </div>
        ) : null}
      </CardContent>
      <CardFooter className="justify-between gap-3 pt-0">
        {isExternalHref ? (
          <a
            className="inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition-colors hover:text-primary"
            href={targetHref}
          >
            Apri dettaglio
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
          </a>
        ) : (
          <Link
            className="inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition-colors hover:text-primary"
            href={targetHref as Route}
          >
            Apri dettaglio
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
          </Link>
        )}
        {showSaveToggle ? <SaveToggle opportunityId={opportunity.id} initialSaved={opportunity.is_saved} /> : null}
      </CardFooter>
    </Card>
  );
}

function scopeLabel(scope: OpportunityCardType['opportunity_scope']) {
  if (scope === 'personal') return 'Personale';
  if (scope === 'business') return 'Attivita';
  return 'Personale + attivita';
}
