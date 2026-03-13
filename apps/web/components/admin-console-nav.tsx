import type { Route } from 'next';
import Link from 'next/link';

const LINKS = [
  { href: '/admin/measure-families', label: 'Famiglie' },
  { href: '/admin/documents', label: 'Documenti' },
  { href: '/admin/survey-coverage', label: 'Survey' },
  { href: '/admin/sources', label: 'Fonti' },
  { href: '/admin/ingestion', label: 'Ingestion' },
  { href: '/admin/review', label: 'Review' },
  { href: '/admin/rules', label: 'Regole' },
] as const satisfies ReadonlyArray<{ href: Route; label: string }>;

export function AdminConsoleNav() {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.8rem' }}>
      {LINKS.map((link) => (
        <Link key={link.href} className="button-secondary" href={link.href}>
          {link.label}
        </Link>
      ))}
    </div>
  );
}
