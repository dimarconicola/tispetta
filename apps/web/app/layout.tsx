import './globals.css';

import type { Metadata, Viewport } from 'next';
import Script from 'next/script';
import { headers } from 'next/headers';

import { Topbar } from '@/components/topbar';
import {
  GA_MEASUREMENT_ID_APEX,
  GA_MEASUREMENT_ID_APP,
  GOOGLE_SITE_VERIFICATION_APEX,
  GOOGLE_SITE_VERIFICATION_APP,
  PUBLIC_APP_URL,
} from '@/lib/env';
import { APEX_HOST, isApexLikeHost } from '@/lib/hosts';
import { getSessionUser } from '@/lib/server-api';

const appSiteUrl = new URL(PUBLIC_APP_URL);

function resolveHostExperience(host: string | null | undefined) {
  const marketingHost = isApexLikeHost(host);
  return {
    marketingHost,
    siteUrl: marketingHost ? new URL(`https://${APEX_HOST}`) : appSiteUrl,
    googleSiteVerification: marketingHost ? GOOGLE_SITE_VERIFICATION_APEX : GOOGLE_SITE_VERIFICATION_APP,
    gaMeasurementId: marketingHost ? GA_MEASUREMENT_ID_APEX : GA_MEASUREMENT_ID_APP,
  };
}

export async function generateMetadata(): Promise<Metadata> {
  const headerStore = await headers();
  const experience = resolveHostExperience(headerStore.get('host'));

  return {
    metadataBase: experience.siteUrl,
    title: {
      default: 'Tispetta',
      template: '%s | Tispetta',
    },
    description: experience.marketingHost
      ? 'Tispetta trasforma fonti ufficiali, norme e pagine operative in una superficie leggibile per startup, freelance e PMI.'
      : 'Tispetta monitora fonti ufficiali italiane e trasforma bandi, incentivi e crediti in opportunita leggibili, verificabili e abbinate al tuo profilo.',
    applicationName: 'Tispetta',
    verification: experience.googleSiteVerification
      ? {
          google: experience.googleSiteVerification,
        }
      : undefined,
    alternates: {
      canonical: '/',
    },
    openGraph: {
      type: 'website',
      locale: 'it_IT',
      url: experience.siteUrl,
      siteName: 'Tispetta',
      title: 'Tispetta',
      description: experience.marketingHost
        ? 'Una superficie chiara per capire incentivi, crediti e agevolazioni italiane senza perdersi tra fonti sparse.'
        : 'Opportunity intelligence per startup, freelance e PMI in Italia, con matching deterministico e fonti ufficiali versionate.',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Tispetta',
      description: experience.marketingHost
        ? 'Leggi gli incentivi italiani come un prodotto: criteri espliciti, fonti verificate, accesso guidato.'
        : 'Scopri bandi, incentivi e crediti rilevanti per il tuo profilo, con fonti ufficiali e spiegazioni verificabili.',
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
}

export const viewport: Viewport = {
  themeColor: '#f5efe2',
  colorScheme: 'light',
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const headerStore = await headers();
  const experience = resolveHostExperience(headerStore.get('host'));
  const user = experience.marketingHost ? null : await getSessionUser().catch(() => null);

  return (
    <html lang="it">
      <body>
        <main className="page-shell">
          <Topbar user={user} variant={experience.marketingHost ? 'marketing' : 'app'} />
          {children}
        </main>
        {experience.gaMeasurementId ? (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${experience.gaMeasurementId}`}
              strategy="afterInteractive"
            />
            <Script id="google-analytics" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${experience.gaMeasurementId}', {
                  page_path: window.location.pathname,
                  page_location: window.location.href,
                  page_title: document.title,
                });
              `}
            </Script>
          </>
        ) : null}
      </body>
    </html>
  );
}
