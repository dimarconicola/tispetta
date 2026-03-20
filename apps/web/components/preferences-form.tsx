'use client';

import { useState, useTransition } from 'react';
import { useForm } from 'react-hook-form';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import type { NotificationPreferences } from '@/lib/types';

const API_URL = '/api/proxy';

const SETTINGS = [
  ['email_enabled', 'Abilita email di prodotto', 'Tutte le comunicazioni transazionali e di monitoraggio.'],
  ['new_opportunity_alerts', 'Nuove opportunita pertinenti', 'Quando un match passa a likely o confirmed.'],
  ['deadline_reminders', 'Promemoria scadenze', 'Quando una scheda rilevante o salvata si avvicina alla deadline.'],
  ['source_change_digests', 'Digest modifiche fonti', 'Quando cambia materialmente una fonte ufficiale collegata a una scheda.'],
  ['weekly_profile_nudges', 'Promemoria completamento profilo', 'Solo quando mancano dati che bloccano opportunita concrete.'],
] as const;

export function PreferencesForm({ preferences }: { preferences: NotificationPreferences | null }) {
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const { register, handleSubmit, setValue, watch } = useForm<NotificationPreferences>({ defaultValues: preferences ?? undefined });

  return (
    <form
      className="grid gap-6"
      onSubmit={handleSubmit((values) => {
        startTransition(async () => {
          const response = await fetch(`${API_URL}/v1/notifications/preferences`, {
            method: 'PUT',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(values),
          });
          setMessage(response.ok ? 'Preferenze salvate.' : 'Salvataggio non riuscito.');
        });
      })}
    >
      <Card>
        <CardHeader className="gap-3">
          <Badge variant="soft" className="w-fit">Notifiche email</Badge>
          <CardTitle className="text-4xl leading-[0.95]">Controlla ritmo e tipologia degli alert.</CardTitle>
          <CardDescription className="max-w-2xl text-base leading-7">
            Le email servono a monitorare opportunita, scadenze e cambi di fonte. Qui scegli solo il ritmo che vuoi ricevere.
          </CardDescription>
        </CardHeader>
      </Card>

      <div className="grid gap-4">
        {SETTINGS.map(([key, title, body]) => (
          <Card key={key}>
            <CardContent className="flex items-start gap-4 py-6">
              <Checkbox
                id={key}
                checked={watch(key)}
                onCheckedChange={(checked) => setValue(key, Boolean(checked), { shouldDirty: true })}
              />
              <div className="grid gap-1">
                <Label htmlFor={key}>{title}</Label>
                <p className="text-sm leading-6 text-slate-600">{body}</p>
              </div>
            </CardContent>
            <input type="hidden" {...register(key)} />
          </Card>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <Button type="submit" className="min-w-[14rem]" disabled={isPending}>
          {isPending ? 'Salvataggio...' : 'Aggiorna preferenze'}
        </Button>
      </div>
      {message ? <div className="banner">{message}</div> : null}
    </form>
  );
}
