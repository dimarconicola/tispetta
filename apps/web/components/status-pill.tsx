import { Badge } from '@/components/ui/badge';
import { cn, statusLabel } from '@/lib/utils';

const statusStyles: Record<string, string> = {
  confirmed: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  likely: 'border-blue-200 bg-blue-50 text-blue-700',
  unclear: 'border-slate-200 bg-slate-100 text-slate-600',
  not_eligible: 'border-rose-200 bg-rose-50 text-rose-700',
};

export function StatusPill({ status }: { status: string | null | undefined }) {
  const safeStatus = status ?? 'unclear';
  return (
    <Badge
      variant="outline"
      className={cn('px-3 py-1 text-[10px] tracking-[0.16em]', statusStyles[safeStatus] ?? statusStyles.unclear)}
    >
      {statusLabel(safeStatus)}
    </Badge>
  );
}
