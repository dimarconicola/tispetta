import { redirect } from 'next/navigation';

import { PreferencesForm } from '@/components/preferences-form';
import { getNotificationPreferences, getSessionUser } from '@/lib/server-api';

export default async function SettingsPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) {
    redirect('/auth/sign-in');
  }

  const preferences = await getNotificationPreferences().catch(() => null);

  return <PreferencesForm preferences={preferences} />;
}
