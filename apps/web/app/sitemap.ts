import type { MetadataRoute } from 'next';

import { INTERNAL_API_URL, PUBLIC_APP_URL } from '@/lib/env';
import type { OpportunityCard } from '@/lib/types';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = PUBLIC_APP_URL.replace(/\/$/, '');
  const now = new Date();
  const opportunities = await fetch(`${INTERNAL_API_URL}/v1/opportunities`, {
    next: { revalidate: 3600 },
  })
    .then(async (response) => {
      if (!response.ok) {
        return [] as OpportunityCard[];
      }
      return (await response.json()) as OpportunityCard[];
    })
    .catch(() => [] as OpportunityCard[]);

  return [
    {
      url: `${baseUrl}/`,
      lastModified: now,
      changeFrequency: 'daily',
      priority: 1,
    },
    {
      url: `${baseUrl}/search`,
      lastModified: now,
      changeFrequency: 'daily',
      priority: 0.8,
    },
    ...opportunities.map((opportunity) => ({
      url: `${baseUrl}/opportunities/${opportunity.slug}`,
      lastModified: new Date(opportunity.last_checked_at),
      changeFrequency: 'daily' as const,
      priority: 0.7,
    })),
  ];
}
