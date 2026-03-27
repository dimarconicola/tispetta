'use client';

import type { Route } from 'next';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
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
      <span className="flex size-10 items-center justify-center rounded-xl border border-[#14110f]/8 bg-[#14110f] text-sm font-bold tracking-tight text-[#fafaf9] shadow-sm shadow-black/10">
        T
      </span>
      <span className="flex min-w-0 flex-col">
        <span className="truncate text-[11px] font-semibold uppercase tracking-[0.18em] text-[#6f6253]">Italy-first opportunity intelligence</span>
        <span className="font-heading text-2xl font-semibold tracking-tight text-[#14110f]">Tispetta</span>
      </span>
    </Link>
  );
}

function NavLink({
  href,
  children,
  emphasized = false,
  prefetch,
  active = false,
}: {
  href: ComponentProps<typeof Link>['href'];
  children: ReactNode;
  emphasized?: boolean;
  prefetch?: boolean;
  active?: boolean;
}) {
  return (
    <Link
      href={href}
      prefetch={prefetch}
      className={cn(
        'inline-flex min-h-10 items-center justify-center rounded-full px-4 text-sm font-medium transition-all duration-200',
        active && !emphasized && 'border-[#14110f]/12 bg-[#14110f] text-[#fafaf9]',
        emphasized
          ? 'border border-[#14110f] bg-[#14110f] text-[#fafaf9] shadow-sm hover:-translate-y-0.5 hover:bg-[#22201d]'
          : 'border border-[#14110f]/10 bg-[#faf6ef] text-[#5f564d] hover:-translate-y-0.5 hover:border-[#14110f]/18 hover:bg-[#f1e7da] hover:text-[#14110f]'
      )}
    >
      {children}
    </Link>
  );
}

export function Topbar({ user, variant = 'app' }: TopbarProps) {
  const pathname = usePathname();

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
        <NavLink href="/" active={pathname === '/'}>I tuoi match</NavLink>
        <NavLink href="/search" active={pathname?.startsWith('/search')}>Cerca</NavLink>
        <NavLink href="/saved" prefetch={false} active={pathname?.startsWith('/saved')}>Salvate</NavLink>
        <NavLink href={'/profile' as Route} prefetch={false} active={pathname?.startsWith('/profile') || pathname?.startsWith('/onboarding')}>Profilo</NavLink>
        <NavLink href="/settings" prefetch={false} active={pathname?.startsWith('/settings')}>Notifiche</NavLink>
        {user?.role === 'admin' ? <NavLink href="/admin/measure-families" prefetch={false} active={pathname?.startsWith('/admin')}>Admin</NavLink> : null}
        {user ? (
          <>
            <form action="/api/auth/sign-out" method="post">
              <button type="submit" className="inline-flex min-h-10 items-center justify-center rounded-full border border-[#14110f]/10 bg-[#faf6ef] px-4 text-sm font-medium text-[#5f564d] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#14110f]/18 hover:bg-[#f1e7da] hover:text-[#14110f]">
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
