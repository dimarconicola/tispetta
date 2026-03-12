import './globals.css';

import type { Metadata } from 'next';

import { Topbar } from '@/components/topbar';
import { getSessionUser } from '@/lib/server-api';

export const metadata: Metadata = {
  title: 'Tispetta',
  description: 'Benefits Opportunity Engine per startup, freelance e PMI in Italia.',
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const user = await getSessionUser().catch(() => null);

  return (
    <html lang="it">
      <body>
        <main className="page-shell">
          <Topbar user={user} />
          {children}
        </main>
      </body>
    </html>
  );
}
