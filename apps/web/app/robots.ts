import type { MetadataRoute } from 'next';

import { PUBLIC_APP_URL } from '@/lib/env';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: ['/', '/search', '/opportunities/'],
        disallow: ['/admin/', '/api/', '/auth/', '/onboarding', '/saved', '/settings'],
      },
    ],
    sitemap: `${PUBLIC_APP_URL}/sitemap.xml`,
    host: PUBLIC_APP_URL,
  };
}
