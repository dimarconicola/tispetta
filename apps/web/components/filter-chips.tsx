import { cn } from '@/lib/utils';

export function FilterChips({
  items,
  active,
  buildHref,
}: {
  items: { label: string; value: string }[];
  active: string | null;
  buildHref: (value: string | null) => string;
}) {
  return (
    <div className="flex flex-wrap gap-2.5">
      <a
        href={buildHref(null)}
        className={cn(
          'inline-flex min-h-11 items-center justify-center rounded-full border px-5 text-sm font-medium transition-all duration-200',
          !active
            ? 'border-slate-900 bg-slate-900 text-white shadow-md shadow-slate-900/10'
            : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900'
        )}
      >
        Tutte
      </a>
      {items.map((item) => (
        <a
          key={item.value}
          href={buildHref(item.value)}
          className={cn(
            'inline-flex min-h-11 items-center justify-center rounded-full border px-5 text-sm font-medium transition-all duration-200',
            active === item.value
              ? 'border-slate-900 bg-slate-900 text-white shadow-md shadow-slate-900/10'
              : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900'
          )}
        >
          {item.label}
        </a>
      ))}
    </div>
  );
}
