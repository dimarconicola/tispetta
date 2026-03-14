import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Tispetta',
    short_name: 'Tispetta',
    description:
      'Opportunity intelligence per startup, freelance e PMI in Italia, con catalogo verificato da fonti ufficiali.',
    start_url: '/',
    display: 'standalone',
    background_color: '#f5efe2',
    theme_color: '#f5efe2',
    lang: 'it-IT',
    icons: [
      {
        src: '/icon.svg',
        sizes: 'any',
        type: 'image/svg+xml',
      },
    ],
  };
}
