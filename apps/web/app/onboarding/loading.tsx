import { RouteLoading } from '@/components/route-loading';

export default function Loading() {
  return (
    <RouteLoading
      eyebrow="Profilo"
      title="Stiamo ricalcolando domande e match"
      body="Chiudiamo lo step attuale, rivalutiamo i blocchi reali e prepariamo il prossimo passaggio del profilo."
    />
  );
}
