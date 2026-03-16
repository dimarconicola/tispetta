'use client';

import { useState, useTransition } from 'react';

const API_URL = '/api/proxy';

export function NotificationRunner() {
  const [reminderMessage, setReminderMessage] = useState<string | null>(null);
  const [digestMessage, setDigestMessage] = useState<string | null>(null);
  const [isReminderPending, startReminderTransition] = useTransition();
  const [isDigestPending, startDigestTransition] = useTransition();

  return (
    <div className="stack">
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div className="stack">
          <button
            type="button"
            className="button"
            disabled={isReminderPending}
            onClick={() => {
              startReminderTransition(async () => {
                setReminderMessage(null);
                const response = await fetch(`${API_URL}/v1/admin/notifications/run-reminders`, {
                  method: 'POST',
                  credentials: 'include',
                });
                if (!response.ok) {
                  setReminderMessage('Invio non riuscito.');
                  return;
                }
                const payload = (await response.json()) as { message: string };
                setReminderMessage(payload.message);
              });
            }}
          >
            {isReminderPending ? 'Invio in corso...' : 'Invia promemoria scadenze'}
          </button>
          {reminderMessage ? <small className="subtle">{reminderMessage}</small> : null}
        </div>

        <div className="stack">
          <button
            type="button"
            className="button-secondary"
            disabled={isDigestPending}
            onClick={() => {
              startDigestTransition(async () => {
                setDigestMessage(null);
                const response = await fetch(`${API_URL}/v1/admin/notifications/run-digest`, {
                  method: 'POST',
                  credentials: 'include',
                });
                if (!response.ok) {
                  setDigestMessage('Invio non riuscito.');
                  return;
                }
                const payload = (await response.json()) as { message: string };
                setDigestMessage(payload.message);
              });
            }}
          >
            {isDigestPending ? 'Invio in corso...' : 'Invia digest settimanale'}
          </button>
          {digestMessage ? <small className="subtle">{digestMessage}</small> : null}
        </div>
      </div>
    </div>
  );
}
