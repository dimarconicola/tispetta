import { redirect } from 'next/navigation';

import { ImpactRail } from '@/components/impact-rail';
import { OpportunityCard } from '@/components/opportunity-card';
import { ProfileForm } from '@/components/profile-form';
import { getOpportunities, getProfile, getProfileQuestions, getSessionUser } from '@/lib/server-api';
import type { ProfileQuestion } from '@/lib/types';

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

  const [profile, questionPayload, opportunities] = await Promise.all([
    getProfile().catch(() => null),
    getProfileQuestions().catch(() => null),
    getOpportunities().catch(() => []),
  ]);

  const requestedStep = Array.isArray(params.step) ? params.step[0] : params.step;
  const currentStep = resolveCurrentStep(questionPayload?.recommended_step, requestedStep, profile);
  const topMatches = opportunities.slice(0, currentStep === 'results' ? 4 : 2);
  const highlightedQuestions = selectHighlightedQuestions(questionPayload, currentStep, profile);

  return (
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(340px,0.75fr)]">
      <div className="grid gap-6">
        <ProfileForm profile={profile} questionPayload={questionPayload} currentStep={currentStep} entry={entry} />

        {currentStep === 'results' ? (
          <section className="grid gap-4">
            <div className="flex items-end justify-between gap-3">
              <div>
                <p className="eyebrow">Prime opportunita</p>
                <h2 className="section-title">I primi match sono gia leggibili</h2>
              </div>
              <span className="text-sm text-slate-500">{topMatches.length} in evidenza</span>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {topMatches.map((opportunity) => (
                <OpportunityCard key={opportunity.id} opportunity={opportunity} />
              ))}
            </div>
          </section>
        ) : null}
      </div>

      <ImpactRail payload={questionPayload} opportunities={topMatches} highlightedQuestions={highlightedQuestions} />
    </section>
  );
}

function resolveCurrentStep(recommendedStep: string | undefined, requestedStep: string | undefined, profile: Awaited<ReturnType<typeof getProfile>>) {
  const factValues = (profile?.fact_values ?? {}) as Record<string, unknown>;
  if (!factValues.profile_type && requestedStep !== 'results' && requestedStep !== 'strategic' && requestedStep !== 'conditional') {
    return 'core_entity';
  }
  if (recommendedStep === 'core_entity') return 'core_entity';
  if (requestedStep === 'results') return 'results';
  if (requestedStep === 'strategic') return 'strategic_intent';
  if (requestedStep === 'conditional') return 'conditional_accuracy';
  if (recommendedStep === 'strategic_intent') return 'strategic_intent';
  if (recommendedStep === 'conditional_accuracy') return 'conditional_accuracy';
  return 'results';
}

function selectHighlightedQuestions(
  payload: Awaited<ReturnType<typeof getProfileQuestions>>,
  currentStep: string,
  profile: Awaited<ReturnType<typeof getProfile>>
): ProfileQuestion[] {
  if (!payload) return [];
  const factValues = (profile?.fact_values ?? {}) as Record<string, unknown>;
  const activeAudiences = ['persona_fisica'];
  const businessType = typeof factValues.profile_type === 'string' && factValues.profile_type !== 'persona_fisica'
    ? factValues.profile_type
    : typeof profile?.user_type === 'string' && profile.user_type !== 'persona_fisica'
      ? profile.user_type
      : null;
  if (businessType) {
    activeAudiences.push(businessType);
  }
  const priorityModules =
    currentStep === 'gate' || currentStep === 'core_entity'
      ? ['strategic_intent', 'conditional_accuracy']
      : currentStep === 'results'
        ? ['strategic_intent', 'conditional_accuracy']
        : currentStep === 'strategic_intent'
          ? ['strategic_intent', 'conditional_accuracy']
          : ['conditional_accuracy'];
  const questions = priorityModules.flatMap(
    (moduleKey) => payload.modules.find((module) => module.key === moduleKey)?.questions ?? []
  );
  return questions
    .filter((question) => !question.audience || question.audience.some((audience) => activeAudiences.includes(audience)))
    .filter((question) => (question.priority ?? 0) > 0)
    .sort(
      (left, right) =>
        (right.upgrade_opportunity_count ?? 0) - (left.upgrade_opportunity_count ?? 0) ||
        (right.blocking_opportunity_count ?? 0) - (left.blocking_opportunity_count ?? 0) ||
        (right.priority ?? 0) - (left.priority ?? 0)
    )
    .slice(0, 3);
}
