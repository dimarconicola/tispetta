import { statusLabel } from '@/lib/utils';

export function StatusPill({ status }: { status: string | null | undefined }) {
  const safeStatus = status ?? 'unclear';
  return (
    <span className="status-pill" data-status={safeStatus}>
      {statusLabel(safeStatus)}
    </span>
  );
}
