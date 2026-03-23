import { RouteLoading } from '@/components/route-loading';

export default function Loading() {
  return (
    <RouteLoading
      eyebrow="Catalogo"
      title="Stiamo aggiornando i risultati"
      body="Ricarichiamo ricerca, filtri e ordinamento senza interrompere il flusso."
    />
  );
}
