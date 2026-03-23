import { RouteLoading } from '@/components/route-loading';

export default function Loading() {
  return (
    <RouteLoading
      eyebrow="Caricamento"
      title="Stiamo aggiornando dashboard e opportunita"
      body="Ricarichiamo dati, ranking e componenti della pagina. La navigazione resta attiva: il contenuto sta solo arrivando."
    />
  );
}
