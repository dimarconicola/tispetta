'use client';

import { Check } from 'lucide-react';

import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

type StepItem = {
  key: string;
  label: string;
  status: 'locked' | 'available' | 'completed';
};

export function QuestionStepper({
  current,
  progress,
  steps,
}: {
  current: string;
  progress: number;
  steps: StepItem[];
}) {
  const renderedSteps = steps.filter((step) => step.status !== 'locked');
  const columnsClass =
    renderedSteps.length <= 2
      ? 'sm:grid-cols-2'
      : renderedSteps.length === 3
        ? 'sm:grid-cols-3'
        : renderedSteps.length === 4
          ? 'sm:grid-cols-4'
          : 'sm:grid-cols-5';

  return (
    <div className="grid gap-3 rounded-[1.35rem] border border-border/70 bg-white/85 p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-medium text-slate-900">Percorso guidato</span>
        <span className="text-slate-500">{Math.round(progress)}%</span>
      </div>
      <Progress value={progress} />
      <div className={cn('grid gap-2', columnsClass)}>
        {renderedSteps.map((step, index) => {
          const isCurrent = step.key === current;
          const isCompleted = step.status === 'completed';
          return (
            <div
              key={step.key}
              className={cn(
                'flex items-center gap-2 rounded-2xl border px-3 py-2 text-xs font-medium',
                isCurrent && 'border-primary bg-blue-50 text-primary',
                isCompleted && 'border-emerald-200 bg-emerald-50 text-emerald-700',
                !isCurrent && !isCompleted && 'border-border bg-background text-muted-foreground'
              )}
            >
              <span
                className={cn(
                  'flex size-6 items-center justify-center rounded-full border text-[11px]',
                  isCurrent && 'border-primary bg-primary text-primary-foreground',
                  isCompleted && 'border-emerald-600 bg-emerald-600 text-white',
                  !isCurrent && !isCompleted && 'border-border bg-white text-muted-foreground'
                )}
              >
                {isCompleted ? <Check className="size-3.5" /> : index + 1}
              </span>
              <span>{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
