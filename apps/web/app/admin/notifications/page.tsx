import { redirect } from 'next/navigation';

import { AdminConsoleNav } from '@/components/admin-console-nav';
import { NotificationRunner } from '@/components/notification-runner';
import { getAdminNotificationHistory, getSessionUser } from '@/lib/server-api';

export default async function AdminNotificationsPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');
  const history = await getAdminNotificationHistory();

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
      <section className="panel stack">
        <div className="stack" style={{ gap: '0.35rem' }}>
          <p className="eyebrow">Storico</p>
          <h2 style={{ fontSize: '1.8rem' }}>Ultime consegne</h2>
          <p className="subtle">Storico centralizzato di eventi, invii riusciti, fallimenti e soppressioni da preferenze.</p>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '820px' }}>
            <thead>
              <tr>
                {['Evento', 'Stato', 'Destinatario', 'Oggetto', 'Creata', 'Inviata', 'Errore'].map((label) => (
                  <th key={label} style={{ textAlign: 'left', padding: '0.75rem 0.5rem', borderBottom: '1px solid rgba(16, 34, 29, 0.12)' }}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.id}>
                  <td style={{ padding: '0.75rem 0.5rem', borderBottom: '1px solid rgba(16, 34, 29, 0.08)' }}>{item.event_type}</td>
                  <td style={{ padding: '0.75rem 0.5rem', borderBottom: '1px solid rgba(16, 34, 29, 0.08)' }}>{item.status}</td>
                  <td style={{ padding: '0.75rem 0.5rem', borderBottom: '1px solid rgba(16, 34, 29, 0.08)' }}>{item.recipient}</td>
                  <td style={{ padding: '0.75rem 0.5rem', borderBottom: '1px solid rgba(16, 34, 29, 0.08)' }}>{item.subject}</td>
                  <td style={{ padding: '0.75rem 0.5rem', borderBottom: '1px solid rgba(16, 34, 29, 0.08)' }}>{new Date(item.created_at).toLocaleString('it-IT')}</td>
                  <td style={{ padding: '0.75rem 0.5rem', borderBottom: '1px solid rgba(16, 34, 29, 0.08)' }}>
                    {item.sent_at ? new Date(item.sent_at).toLocaleString('it-IT') : '—'}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', borderBottom: '1px solid rgba(16, 34, 29, 0.08)' }}>{item.error_message ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
