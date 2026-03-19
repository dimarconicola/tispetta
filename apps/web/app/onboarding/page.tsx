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

  const requestedStep = Array.isArray(params.step) ? params.step[0] : params.step;
  const coreQuestions = questions.filter((question) => question.module === 'core_entity');
  const conditionalQuestions = questions.filter((question) => question.module === 'conditional_accuracy');
  const coreComplete = coreQuestions.every((question) => hasProfileValue(profile, question.key));
  const currentStep = !coreComplete
    ? 'core'
    : requestedStep === 'conditional'
      ? 'conditional'
      : 'strategic';
  const visibleOpportunities = coreComplete ? opportunities.slice(0, 4) : [];
  const blockedCount = visibleOpportunities.filter((item) => item.match_status === 'unclear' || item.missing_fields.length > 0).length;

  return (
    <div className="split">
      <ProfileForm profile={profile} questions={questions} currentStep={currentStep} entry={entry} />
      <div className="stack">
        <div className="panel stack">
          {!coreComplete ? (
            <>
              <p className="eyebrow">Step 1 di 3</p>
              <h2 style={{ fontSize: '2.2rem' }}>Chiudi il core, poi vedi subito i match utili.</h2>
              <div className="stack subtle">
                <p>Il primo passaggio resta entro 8 domande obbligatorie: perimetro attivita, forma, regione, settore, dimensione e regime innovativo.</p>
                <p>Non ti chiediamo assunzioni, export o dati sensibili finche non servono davvero a chiarire una misura.</p>
              </div>
            </>
          ) : isMarketingEntry ? (
            <>
              <p className="eyebrow">Ingresso guidato</p>
              <h2 style={{ fontSize: '2.2rem' }}>Hai gia il perimetro. Ora decidi quanta precisione aggiungere.</h2>
              <div className="stack subtle">
                <p>I primi risultati sono gia disponibili. I moduli successivi servono a far salire i match da unclear o likely verso confirmed.</p>
                <p>Assunzioni, export, energia e altri rami restano opzionali: li apri solo se vuoi coprire quelle famiglie di misura.</p>
              </div>
            </>
          ) : (
            <>
              <p className="eyebrow">Risultati live</p>
              <h2 style={{ fontSize: '2.2rem' }}>Hai gia una prima lettura. Ora puoi aumentare la precisione.</h2>
              <p className="subtle">
                Il motore ricalcola i match dopo ogni salvataggio. Le domande successive servono solo a migliorare ranking e stato, non a sbloccare l&apos;accesso al prodotto.
              </p>
            </>
          )}
        </div>
        {coreComplete ? (
          <>
            <div className="panel stack">
              <p className="eyebrow">Snapshot immediato</p>
              <h3 style={{ fontSize: '1.7rem' }}>{visibleOpportunities.length} opportunita prioritarie disponibili ora</h3>
              <p className="subtle">
                {blockedCount > 0
                  ? `${blockedCount} hanno ancora campi mancanti o uno stato unclear: le domande successive servono a chiarirle.`
                  : 'I match principali sono gia leggibili. Continua solo se vuoi rifinire ranking e coverage.'}
              </p>
            </div>
            {visibleOpportunities.map((opportunity) => (
              <OpportunityCard key={opportunity.id} opportunity={opportunity} />
            ))}
            {conditionalQuestions.length > 0 ? (
              <div className="banner">Le domande di precisione si attivano solo quando una famiglia di misure reale le richiede.</div>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}

function hasProfileValue(profile: Awaited<ReturnType<typeof getProfile>>, key: string): boolean {
  const factValues = (profile?.fact_values ?? {}) as Record<string, unknown>;
  const value = factValues[key];
  return value !== undefined && value !== null && value !== '';
}
