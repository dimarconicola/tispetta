import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return 'Nessuna scadenza definita';
  return new Intl.DateTimeFormat('it-IT', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value));
}

export function formatCurrency(value: number | null | undefined): string {
  if (!value) return 'Valore da verificare';
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value);
}

export function statusLabel(status: string | null | undefined): string {
  switch (status) {
    case 'confirmed':
      return 'Confermato';
    case 'likely':
      return 'Compatibile';
    case 'unclear':
      return 'Da chiarire';
    case 'not_eligible':
      return 'Fuori profilo';
    default:
      return 'Da valutare';
  }
}

export function categoryLabel(category: string): string {
  return category
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatCompactDateTime(value: string | null | undefined): string {
  if (!value) return 'n/d';
  return new Intl.DateTimeFormat('it-IT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/Rome',
  }).format(new Date(value));
}
