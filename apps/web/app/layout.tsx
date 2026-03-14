import './globals.css';

import type { Metadata, Viewport } from 'next';
import Script from 'next/script';

import { Topbar } from '@/components/topbar';
import { GA_MEASUREMENT_ID, GOOGLE_SITE_VERIFICATION, PUBLIC_APP_URL } from '@/lib/env';
import { getSessionUser } from '@/lib/server-api';

const siteUrl = new URL(PUBLIC_APP_URL);

export const metadata: Metadata = {
  metadataBase: siteUrl,
  title: {
    default: 'Tispetta',
    template: '%s | Tispetta',
  },
  description:
    'Tispetta monitora fonti ufficiali italiane e trasforma bandi, incentivi e crediti in opportunita leggibili, verificabili e abbinate al tuo profilo.',
  applicationName: 'Tispetta',
  verification: GOOGLE_SITE_VERIFICATION
    ? {
        google: GOOGLE_SITE_VERIFICATION,
      }
    : undefined,
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'it_IT',
    url: siteUrl,
    siteName: 'Tispetta',
    title: 'Tispetta',
    description:
      'Opportunity intelligence per startup, freelance e PMI in Italia, con matching deterministico e fonti ufficiali versionate.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Tispetta',
    description:
      'Scopri bandi, incentivi e crediti rilevanti per il tuo profilo, con fonti ufficiali e spiegazioni verificabili.',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1,
      'max-video-preview': -1,
    },
  },
};

export const viewport: Viewport = {
  themeColor: '#f5efe2',
  colorScheme: 'light',
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
        {GA_MEASUREMENT_ID ? (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
              strategy="afterInteractive"
            />
            <Script id="google-analytics" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${GA_MEASUREMENT_ID}', {
                  page_path: window.location.pathname,
                });
              `}
            </Script>
          </>
        ) : null}
      </body>
    </html>
  );
}
