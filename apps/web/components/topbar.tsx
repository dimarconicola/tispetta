import Link from 'next/link';
import type { ComponentProps, ReactNode } from 'react';

import { cn } from '@/lib/utils';
import type { SessionUser } from '@/lib/types';

type TopbarProps = {
  user: SessionUser | null;
  variant?: 'app' | 'marketing';
};

function Brand({ href }: { href: ComponentProps<typeof Link>['href'] }) {
  return (
    <Link href={href} className="flex items-center gap-3">
      <span className="flex size-10 items-center justify-center rounded-2xl bg-primary text-sm font-bold tracking-tight text-primary-foreground shadow-sm shadow-primary/20">
        T
      </span>
      <span className="flex min-w-0 flex-col">
        <span className="truncate text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">Italy-first opportunity intelligence</span>
        <span className="font-heading text-2xl font-semibold tracking-tight text-foreground">Tispetta</span>
      </span>
    </Link>
  );
}

function NavLink({
  href,
  children,
  emphasized = false,
}: {
  href: ComponentProps<typeof Link>['href'];
  children: ReactNode;
  emphasized?: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        'inline-flex min-h-10 items-center justify-center rounded-full px-4 text-sm font-medium transition-all duration-200',
        emphasized
          ? 'border border-transparent bg-primary text-primary-foreground shadow-sm hover:-translate-y-0.5 hover:bg-primary/92'
          : 'border border-border bg-card text-muted-foreground hover:-translate-y-0.5 hover:border-border/90 hover:bg-accent/50 hover:text-foreground'
      )}
    >
      {children}
    </Link>
  );
}

export function Topbar({ user, variant = 'app' }: TopbarProps) {
  if (variant === 'marketing') {
    return (
      <header className="topbar">
        <Brand href="/" />
        <nav className="nav hidden lg:flex">
          <NavLink href="/#accesso">Ingresso</NavLink>
          <NavLink href="/#metodo">Metodo</NavLink>
          <NavLink href="/#copertura">Copertura</NavLink>
          <NavLink href="/#per-chi">Per chi</NavLink>
          <NavLink href="https://app.tispetta.eu/search">Catalogo live</NavLink>
          <NavLink href="https://app.tispetta.eu/start" emphasized>
            Inizia guidato
          </NavLink>
        </nav>
      </header>
    );
  }

  return (
    <header className="topbar">
      <Brand href="/" />
      <nav className="nav">
        <NavLink href="/search">Cerca</NavLink>
        <NavLink href="/saved">Salvate</NavLink>
        <NavLink href="/onboarding">Profilo</NavLink>
        <NavLink href="/settings">Notifiche</NavLink>
        {user?.role === 'admin' ? <NavLink href="/admin/measure-families">Admin</NavLink> : null}
        {user ? (
          <>
            <form action="/api/auth/sign-out" method="post">
              <button type="submit" className="inline-flex min-h-10 items-center justify-center rounded-full border border-border bg-card px-4 text-sm font-medium text-muted-foreground transition-all duration-200 hover:-translate-y-0.5 hover:border-border/90 hover:bg-accent/50 hover:text-foreground">
                Esci
              </button>
            </form>
          </>
        ) : (
          <NavLink href="/auth/sign-in" emphasized>
            Accedi
          </NavLink>
        )}
      </nav>
    </header>
  );
}
