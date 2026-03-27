import { redirect } from 'next/navigation';

import { OnboardingRail } from '@/components/onboarding-rail';
import { ProfileForm } from '@/components/profile-form';
import { getProfile, getProfileQuestions, getSessionUser } from '@/lib/server-api';

export default async function OnboardingPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const entry = Array.isArray(params.entry) ? params.entry[0] : params.entry;
  const requestedStep = Array.isArray(params.step) ? params.step[0] : params.step;
  const requestedModule = Array.isArray(params.module) ? params.module[0] : params.module;
  const returnTo = Array.isArray(params.return_to) ? params.return_to[0] : params.return_to;
  const isMarketingEntry = entry === 'apex';
  const user = await getSessionUser().catch(() => null);
  if (!user) {
    redirect(isMarketingEntry ? '/start' : '/auth/sign-in');
  }

  const [profile, questionPayload] = await Promise.all([
    getProfile().catch(() => null),
    getProfileQuestions({ step: requestedStep, module: requestedModule }).catch(() => null),
  ]);

  return (
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
      <ProfileForm profile={profile} questionPayload={questionPayload} entry={entry} returnTo={returnTo} />
      <OnboardingRail payload={questionPayload} />
    </section>
  );
}
