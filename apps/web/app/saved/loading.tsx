import { RouteLoading } from '@/components/route-loading';

export default function Loading() {
  return (
    <RouteLoading
      eyebrow="Shortlist"
      title="Stiamo recuperando le opportunita salvate"
      body="Riuniamo la tua shortlist con stato, priorita e aggiornamenti piu recenti."
    />
  );
}
