import { redirect } from 'next/navigation';

import { OpportunityCard } from '@/components/opportunity-card';
import { ProfileForm } from '@/components/profile-form';
import { getOpportunities, getProfile, getProfileQuestions, getSessionUser } from '@/lib/server-api';

export default async function OnboardingPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) {
    redirect('/auth/sign-in');
  }

  const [profile, questions, opportunities] = await Promise.all([
    getProfile().catch(() => null),
    getProfileQuestions().catch(() => []),
    getOpportunities().catch(() => []),
  ]);

  return (
    <div className="split">
      <ProfileForm profile={profile} questions={questions} />
      <div className="stack">
        <div className="panel stack">
          <p className="eyebrow">Effetto immediato</p>
          <h2 style={{ fontSize: '2.2rem' }}>Ogni dato in piu puo cambiare ranking e stato.</h2>
          <p className="subtle">
            Il motore ricalcola i match dopo ogni salvataggio e rende espliciti i campi ancora mancanti.
          </p>
        </div>
        {opportunities.slice(0, 3).map((opportunity) => (
          <OpportunityCard key={opportunity.id} opportunity={opportunity} />
        ))}
      </div>
    </div>
  );
}
