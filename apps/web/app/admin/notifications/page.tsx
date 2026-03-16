import { redirect } from 'next/navigation';

import { AdminConsoleNav } from '@/components/admin-console-nav';
import { NotificationRunner } from '@/components/notification-runner';
import { getSessionUser } from '@/lib/server-api';

export default async function AdminNotificationsPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Admin</p>
        <h1 style={{ fontSize: '3rem' }}>Notifiche</h1>
        <p className="subtle">Invia manualmente le email di notifica agli utenti con le preferenze abilitate.</p>
        <AdminConsoleNav />
      </section>
      <section className="panel stack">
        <h2 style={{ fontSize: '1.8rem' }}>Promemoria scadenze</h2>
        <p className="subtle">Invia un riepilogo delle opportunita confermate o probabili con scadenza entro 30 giorni. Solo agli utenti con deadline_reminders abilitato.</p>
        <NotificationRunner />
      </section>
    </div>
  );
}
