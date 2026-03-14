import type { MetadataRoute } from 'next';
import { headers } from 'next/headers';

import { APEX_HOST, APP_HOST, isApexLikeHost } from '@/lib/hosts';

export default async function robots(): Promise<MetadataRoute.Robots> {
  const host = (await headers()).get('host');
  const marketingHost = isApexLikeHost(host);
  const baseUrl = `https://${marketingHost ? APEX_HOST : APP_HOST}`;

  return {
    rules: [
      marketingHost
        ? {
            userAgent: '*',
            allow: ['/'],
            disallow: ['/search', '/opportunities/', '/admin/', '/api/', '/auth/', '/onboarding', '/saved', '/settings'],
          }
        : {
            userAgent: '*',
            allow: ['/', '/search', '/opportunities/'],
            disallow: ['/admin/', '/api/', '/auth/', '/onboarding', '/saved', '/settings'],
          },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  };
}
