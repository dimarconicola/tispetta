import type { Route } from 'next';
import Link from 'next/link';
import { Check } from 'lucide-react';

import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

const STEP_LABELS = [
  { key: 'core_entity', label: 'Profilo' },
  { key: 'results', label: 'Prime misure' },
  { key: 'strategic_intent', label: 'Progetti' },
  { key: 'conditional_accuracy', label: 'Dettagli finali' },
];

export function QuestionStepper({
  current,
  progress,
  hrefForStep,
  visibleSteps,
}: {
  current: string;
  progress: number;
  hrefForStep?: (stepKey: string) => Route | null;
  visibleSteps?: string[];
}) {
  const renderedSteps = visibleSteps?.length
    ? STEP_LABELS.filter((step) => visibleSteps.includes(step.key))
    : STEP_LABELS;

  return (
    <div className="grid gap-4 rounded-[1.75rem] border border-border/70 bg-white/80 p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-medium text-slate-900">Progressione</span>
        <span className="text-slate-500">{Math.round(progress)}%</span>
      </div>
      <Progress value={progress} />
      <div className="grid gap-2 sm:grid-cols-4 sm:gap-3">
        {renderedSteps.map((step, index) => {
          const active = step.key === current;
          const completed = index < renderedSteps.findIndex((item) => item.key === current);
          const href = hrefForStep?.(step.key) ?? null;
          const className = cn(
            'flex items-center gap-2 rounded-2xl border px-3 py-3 text-xs font-medium transition-colors',
            active && 'border-primary bg-blue-50 text-primary',
            completed && 'border-emerald-200 bg-emerald-50 text-emerald-700',
            !active && !completed && 'border-border bg-background text-muted-foreground',
            href && 'hover:-translate-y-0.5 hover:shadow-sm'
          );
          const inner = (
            <>
              <span
                className={cn(
                  'flex size-6 items-center justify-center rounded-full border text-[11px]',
                  active && 'border-primary bg-primary text-primary-foreground',
                  completed && 'border-emerald-600 bg-emerald-600 text-white',
                  !active && !completed && 'border-border bg-white text-muted-foreground'
                )}
              >
                {completed ? <Check className="size-3.5" /> : index + 1}
              </span>
              <span>{step.label}</span>
            </>
          );
          return href ? (
            <Link key={step.key} href={href} className={className}>
              {inner}
            </Link>
          ) : (
            <div key={step.key} className={className}>
              {inner}
            </div>
          );
        })}
      </div>
    </div>
  );
}
