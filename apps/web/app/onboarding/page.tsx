import { redirect } from 'next/navigation';

import { OpportunityCard } from '@/components/opportunity-card';
import { ProfileForm } from '@/components/profile-form';
import { getOpportunities, getProfile, getProfileQuestions, getSessionUser } from '@/lib/server-api';

export default async function OnboardingPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const entry = Array.isArray(params.entry) ? params.entry[0] : params.entry;
  const isMarketingEntry = entry === 'apex';
  const user = await getSessionUser().catch(() => null);
  if (!user) {
    redirect(isMarketingEntry ? '/start' : '/auth/sign-in');
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
          {isMarketingEntry ? (
            <>
              <p className="eyebrow">Ingresso guidato</p>
              <h2 style={{ fontSize: '2.2rem' }}>Parti dai fatti stabili. Il resto si apre solo se serve.</h2>
              <div className="stack subtle">
                <p>Prima raccogliamo il nucleo che sposta davvero i match: fase attivita, forma legale, regione, dimensione, settore e regime innovativo.</p>
                <p>Il questionario core resta entro 8 domande. Moduli su assunzioni, export o investimenti entrano solo quando servono a una famiglia di misure reale.</p>
              </div>
            </>
          ) : (
            <>
              <p className="eyebrow">Effetto immediato</p>
              <h2 style={{ fontSize: '2.2rem' }}>Ogni dato in piu puo cambiare ranking e stato.</h2>
              <p className="subtle">
                Il motore ricalcola i match dopo ogni salvataggio e rende espliciti i campi ancora mancanti.
              </p>
            </>
          )}
        </div>
        {opportunities.slice(0, 3).map((opportunity) => (
          <OpportunityCard key={opportunity.id} opportunity={opportunity} />
        ))}
      </div>
    </div>
  );
}
