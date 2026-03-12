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
      return 'Probabile';
    case 'unclear':
      return 'Da chiarire';
    case 'not_eligible':
      return 'Non idoneo';
    default:
      return 'Da valutare';
  }
}

export function categoryLabel(category: string): string {
  return category
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
