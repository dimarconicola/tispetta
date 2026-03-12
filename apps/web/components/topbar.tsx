import Link from 'next/link';

import type { SessionUser } from '@/lib/types';

export function Topbar({ user }: { user: SessionUser | null }) {
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
        {user?.role === 'admin' ? <Link href="/admin/sources">Admin</Link> : null}
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
