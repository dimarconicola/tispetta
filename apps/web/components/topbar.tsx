import Link from 'next/link';

import type { SessionUser } from '@/lib/types';

type TopbarProps = {
  user: SessionUser | null;
  variant?: 'app' | 'marketing';
};

export function Topbar({ user, variant = 'app' }: TopbarProps) {
  if (variant === 'marketing') {
    return (
      <header className="topbar topbar-marketing">
        <Link href="/" className="brand">
          <span className="brand-mark">Italy-first opportunity intelligence</span>
          <span className="brand-name">Tispetta</span>
        </Link>
        <nav className="nav">
          <Link href="/#metodo">Metodo</Link>
          <Link href="/#copertura">Copertura</Link>
          <Link href="/#per-chi">Per chi</Link>
          <Link href="https://app.tispetta.eu/search">Catalogo live</Link>
          <Link href="https://app.tispetta.eu/auth/sign-in" className="button-secondary">
            Apri l&apos;app
          </Link>
        </nav>
      </header>
    );
  }

  return (
    <header className="topbar">
      <Link href="/" className="brand">
        <span className="brand-mark">Italy-first opportunity intelligence</span>
        <span className="brand-name">Tispetta</span>
      </Link>
      <nav className="nav">
        <Link href="/search">Esplora</Link>
        <Link href="/onboarding">Profilo</Link>
        <Link href="/saved">Salvate</Link>
        <Link href="/settings">Notifiche</Link>
        {user?.role === 'admin' ? <Link href="/admin/measure-families">Admin</Link> : null}
        {user ? (
          <>
            <Link href="/onboarding">Area personale</Link>
            <form action="/api/auth/sign-out" method="post">
              <button type="submit" className="nav-button">
                Esci
              </button>
            </form>
          </>
        ) : (
          <Link href="/auth/sign-in">Accedi</Link>
        )}
      </nav>
    </header>
  );
}
