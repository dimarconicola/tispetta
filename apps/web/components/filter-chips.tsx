import type { Route } from 'next';
import Link from 'next/link';

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
      <Link
        href={buildHref(null) as Route}
        className={cn(
          'inline-flex min-h-11 items-center justify-center rounded-full border px-5 text-sm font-medium transition-all duration-200',
          !active
            ? 'border-[#14110f] bg-[#14110f] !text-[#fafaf9] shadow-md shadow-black/10 hover:bg-[#22201d] hover:!text-[#fafaf9]'
            : 'border-[#14110f]/10 bg-[#faf6ef] text-[#5f564d] hover:border-[#14110f]/18 hover:bg-[#f1e7da] hover:text-[#14110f]'
        )}
      >
        Tutte
      </Link>
      {items.map((item) => (
        <Link
          key={item.value}
          href={buildHref(item.value) as Route}
          className={cn(
            'inline-flex min-h-11 items-center justify-center rounded-full border px-5 text-sm font-medium transition-all duration-200',
            active === item.value
              ? 'border-[#14110f] bg-[#14110f] !text-[#fafaf9] shadow-md shadow-black/10 hover:bg-[#22201d] hover:!text-[#fafaf9]'
              : 'border-[#14110f]/10 bg-[#faf6ef] text-[#5f564d] hover:border-[#14110f]/18 hover:bg-[#f1e7da] hover:text-[#14110f]'
          )}
        >
          {item.label}
        </Link>
      ))}
    </div>
  );
}
