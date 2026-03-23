import type { Route } from 'next';
import Link from 'next/link';
import { ArrowRight, Search, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

export function SearchBar({
  action = '/search',
  defaultValue,
  placeholder = 'Cerca incentivi, bonus, crediti o bisogni concreti...',
  className,
}: {
  action?: string;
  defaultValue?: string;
  placeholder?: string;
  className?: string;
}) {
  return (
    <form action={action} className={cn('group relative w-full max-w-4xl', className)}>
      <Search className="pointer-events-none absolute left-5 top-1/2 size-5 -translate-y-1/2 text-slate-400 transition-colors group-focus-within:text-primary" />
      <Input
        name="query"
        defaultValue={defaultValue}
        placeholder={placeholder}
        className="h-16 rounded-[1.75rem] border-slate-200 bg-white pl-14 pr-36 text-base shadow-sm placeholder:text-slate-400"
      />
      {defaultValue ? <input type="hidden" name="_has_query" value="1" /> : null}
      <div className="absolute inset-y-0 right-3 flex items-center gap-2">
        {defaultValue ? (
          <Button asChild size="icon" variant="ghost" className="size-10 rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-700">
            <Link href={action as Route} aria-label="Pulisci ricerca">
              <X className="size-4" />
            </Link>
          </Button>
        ) : null}
        <Button type="submit" className="h-11 px-5">
          Cerca
          <ArrowRight className="size-4" />
        </Button>
      </div>
    </form>
  );
}
