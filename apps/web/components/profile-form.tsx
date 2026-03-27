'use client';

import type { Route } from 'next';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, BriefcaseBusiness, CheckCircle2, CircleHelp, Sparkles, UserRound } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';

import { OpportunityCard } from '@/components/opportunity-card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { NativeSelect } from '@/components/ui/native-select';
import { Textarea } from '@/components/ui/textarea';
import { buildOnboardingHref, type OnboardingStepKey, formatOptionLabel } from '@/lib/profile-ui';
import type { Profile, ProfileQuestion, ProfileQuestionResponse } from '@/lib/types';

import { QuestionStepper } from './question-stepper';

const API_URL = '/api/proxy';

type FormValues = Record<string, string | boolean | null>;

const BUSINESS_TYPE_OPTIONS = [
  {
    value: 'freelancer',
    label: 'Freelance o partita IVA',
    body: 'Professionista, autonomo o attivita individuale.',
  },
  {
    value: 'startup',
    label: 'Startup o nuova impresa',
    body: 'Stai aprendo o hai una realta giovane e in crescita.',
  },
  {
    value: 'sme',
    label: 'PMI o societa attiva',
    body: 'Hai gia una struttura operativa o una societa avviata.',
  },
];

const BUSINESS_FACT_KEYS_TO_CLEAR = [
  'activity_stage',
  'legal_form_bucket',
  'company_age_or_formation_window',
  'size_band',
  'sector_macro_category',
  'innovation_regime_status',
  'hiring_interest',
  'export_investment_intent',
  'digital_transition_project',
  'energy_transition_project',
  'women_led_majority',
  'founder_age_band',
  'unemployment_status_at_start',
  'no_prior_permanent_employment',
  'target_hire_age_band',
  'target_hire_gender_priority',
  'target_hire_disadvantaged_status',
  'target_market_scope',
  'energy_reduction_goal',
  'filed_balance_sheets_count',
  'patent_ip_intent',
];

export function ProfileForm({
  profile,
  questionPayload,
  entry,
  returnTo,
}: {
  profile: Profile | null;
  questionPayload: ProfileQuestionResponse | null;
  entry?: string;
  returnTo?: string;
}) {
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const hasMountedRef = useRef(false);
  const initialValues = useMemo(() => buildInitialValues(profile), [profile]);
  const { register, handleSubmit, reset } = useForm<FormValues>({ defaultValues: initialValues });
  const currentStep = (questionPayload?.journey.current_step ?? 'personal_core') as OnboardingStepKey;
  const steps = questionPayload?.journey.steps ?? [];
  const progressPercent = computeWizardProgress(questionPayload);
  const currentModule = useMemo(() => {
    if (!questionPayload?.strategic_modules?.length) return null;
    return (
      questionPayload.strategic_modules.find((module) => module.key === questionPayload.journey.active_module_key) ??
      questionPayload.strategic_modules[0]
    );
  }, [questionPayload]);
  const [businessMode, setBusinessMode] = useState<'none' | 'enabled'>(() =>
    questionPayload?.business_context.enabled ? 'enabled' : 'none'
  );
  const [selectedBusinessType, setSelectedBusinessType] = useState<string>(
    questionPayload?.business_context.profile_type ?? resolveBusinessType(profile) ?? 'startup'
  );

  useEffect(() => {
    if (!hasMountedRef.current) {
      hasMountedRef.current = true;
      return;
    }
    reset(initialValues);
    setMessage(null);
    setIsSubmitting(false);
  }, [initialValues, reset]);

  useEffect(() => {
    setBusinessMode(questionPayload?.business_context.enabled ? 'enabled' : 'none');
    setSelectedBusinessType(questionPayload?.business_context.profile_type ?? resolveBusinessType(profile) ?? 'startup');
  }, [profile, questionPayload]);

  const personalQuestions = questionPayload?.personal_core_questions ?? [];
  const businessQuestions = questionPayload?.business_core_questions ?? [];
  const currentQuestions = currentStep === 'personal_core'
    ? personalQuestions
    : currentStep === 'business_core'
      ? businessQuestions
      : currentStep === 'strategic_modules'
        ? currentModule?.questions ?? []
        : [];

  const primaryHref = questionPayload
    ? computePrimaryHref(currentStep, questionPayload, entry, businessMode, returnTo)
    : buildOnboardingHref('personal_core', undefined, entry, returnTo);
  const backHref = questionPayload ? computeBackHref(currentStep, questionPayload, entry, returnTo) : undefined;

  if (!questionPayload) {
    return (
      <Card>
        <CardContent className="py-10 text-sm leading-7 text-slate-600">
          Non riusciamo a caricare il percorso in questo momento. Ricarica la pagina tra un attimo.
        </CardContent>
      </Card>
    );
  }

  if (currentStep === 'results_checkpoint') {
    return (
      <div className="grid gap-5">
        <QuestionStepper current={currentStep} progress={progressPercent} steps={steps} />
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="soft" className="w-fit">Prime misure</Badge>
            <CardTitle className="text-4xl leading-[0.95]">Adesso hai gia un primo set leggibile.</CardTitle>
            <CardDescription className="max-w-3xl text-base leading-7">
              Il profilo iniziale e sufficiente per farti vedere cosa emerge adesso. Da qui in poi puoi solo migliorare precisione e dettaglio.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5">
            <div className="grid gap-4 rounded-[1.6rem] border border-border/70 bg-slate-50/85 p-5">
              <div className="flex items-center gap-2 text-primary">
                <Sparkles className="size-4" />
                <span className="text-sm font-semibold">{questionPayload.results_summary.profile_state}</span>
              </div>
              <p className="text-sm leading-7 text-slate-600">
                {questionPayload.results_summary.total_matches > 0
                  ? `Stiamo gia mostrando ${questionPayload.results_summary.total_matches} opportunita ordinate in modo coerente con il tuo profilo.`
                  : 'Il profilo e salvato. Il riepilogo dei match si sta riallineando con i dati appena registrati.'}
              </p>
            </div>

            {questionPayload.results_summary.top_matches.length ? (
              <div className="grid gap-4 md:grid-cols-2">
                {questionPayload.results_summary.top_matches.map((opportunity) => (
                  <OpportunityCard key={opportunity.id} opportunity={opportunity} />
                ))}
              </div>
            ) : (
              <div className="rounded-[1.5rem] border border-blue-100 bg-blue-50/80 p-5 text-sm leading-7 text-blue-950">
                Le prime misure stanno arrivando. Ricarica tra un attimo oppure apri il catalogo completo.
              </div>
            )}

            <div className="grid gap-3 rounded-[1.6rem] border border-border/70 bg-white/85 p-5">
              <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cosa puoi chiarire dopo</span>
              <div className="flex flex-wrap gap-2">
                {questionPayload.results_summary.next_focus_labels.length ? (
                  questionPayload.results_summary.next_focus_labels.map((label) => (
                    <Badge key={label} variant="outline">{label}</Badge>
                  ))
                ) : (
                  <Badge variant="outline">Nessun passaggio extra obbligatorio</Badge>
                )}
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              {questionPayload.strategic_modules.length ? (
                <button type="button" className="button" onClick={() => window.location.assign(primaryHref)}>
                  Continua a rifinire il profilo
                  <ArrowRight className="size-4" />
                </button>
              ) : (
                <Link className="button" href={'/' as Route}>
                  Vai ai tuoi match
                  <ArrowRight className="size-4" />
                </Link>
              )}
              {questionPayload.strategic_modules.length ? (
                <Link className="button-secondary" href={'/' as Route}>
                  Vai ai tuoi match
                </Link>
              ) : null}
              <Link className="button-secondary" href={buildSearchHref() as Route}>
                Apri il catalogo generale
              </Link>
              {returnTo ? <Link className="button-secondary" href={returnTo as Route}>Torna al profilo</Link> : null}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (currentStep === 'final_next_actions') {
    return (
      <div className="grid gap-5">
        <QuestionStepper current={currentStep} progress={progressPercent} steps={steps} />
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="soft" className="w-fit">Passaggio completato</Badge>
            <CardTitle className="text-4xl leading-[0.95]">Il profilo e gia utilizzabile.</CardTitle>
            <CardDescription className="max-w-3xl text-base leading-7">
              Hai chiuso i passaggi essenziali. Puoi tornare qui quando vuoi per rivedere il profilo oppure continuare nel catalogo live.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5">
            <div className="grid gap-3 rounded-[1.6rem] border border-emerald-200 bg-emerald-50/80 p-5 text-sm leading-7 text-emerald-950">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="size-4" />
                <span className="font-semibold">{questionPayload.results_summary.profile_state}</span>
              </div>
              <p>
                Hai un feed unico che mette insieme opportunita personali e, se presenti, anche quelle per la tua attivita.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link className="button" href={'/' as Route}>
                Vai ai tuoi match
                <ArrowRight className="size-4" />
              </Link>
              <Link className="button-secondary" href={buildSearchHref() as Route}>
                Apri il catalogo generale
              </Link>
              <Link className="button-secondary" href={'/profile' as Route}>Apri il profilo</Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const copy = stepCopy(currentStep, currentModule?.title);

  return (
    <form
      className="grid gap-5"
      onSubmit={handleSubmit(async (values) => {
        setMessage(null);
        setIsSubmitting(true);
        const payload = buildPayloadForStep({
          currentStep,
          currentQuestions,
          values,
          businessMode,
          selectedBusinessType,
          profile,
        });

        const response = await fetch(`${API_URL}/v1/profile`, {
          method: 'PUT',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          if (response.status === 401) {
            window.location.assign('/auth/sign-in?reason=session-expired');
            return;
          }
          setMessage('Aggiornamento non riuscito. Riprova tra qualche secondo.');
          setIsSubmitting(false);
          return;
        }

        setIsSubmitting(false);
        window.location.assign(primaryHref);
      })}
    >
      <QuestionStepper current={currentStep} progress={progressPercent} steps={steps} />

      <Card>
        <CardHeader className="gap-3">
          <Badge variant="soft" className="w-fit">{copy.eyebrow}</Badge>
          <CardTitle className="text-4xl leading-[0.95]">{copy.title}</CardTitle>
          <CardDescription className="max-w-3xl text-base leading-7">{copy.body}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <NarrativeStat
            label="Profilo personale"
            value={`${questionPayload.progress_summary.personal_answered}/${questionPayload.progress_summary.personal_total}`}
            body="Questa parte resta sempre la base. Regione, lavoro, fascia di eta e nucleo spostano molti esiti."
          />
          <NarrativeStat
            label="Attivita"
            value={
              questionPayload.business_context.answered
                ? questionPayload.business_context.enabled
                  ? businessTypeLabel(questionPayload.business_context.profile_type)
                  : 'Non aggiunta'
                : 'Da confermare'
            }
            body="La aggiungi solo se ti serve. Il feed tiene insieme opportunita personali e, se serve, anche d impresa."
          />
          <NarrativeStat
            label="Feed personalizzato"
            value={String(questionPayload.results_summary.total_matches)}
            body="Dopo i passaggi iniziali vai nei tuoi match. Gli approfondimenti dopo servono solo a chiarire meglio."
          />
        </CardContent>
      </Card>

      {currentStep === 'personal_core' ? (
        <Card>
          <CardHeader className="gap-3">
            <div className="flex items-center gap-3">
              <span className="flex size-12 items-center justify-center rounded-2xl bg-blue-50 text-primary">
                <UserRound className="size-5" />
              </span>
              <div className="grid gap-1">
                <Badge variant="outline" className="w-fit">Profilo personale</Badge>
                <CardTitle className="text-2xl">Partiamo da te</CardTitle>
              </div>
            </div>
            <CardDescription className="max-w-3xl text-base leading-7">
              Partiamo dalle informazioni personali che incidono davvero sui risultati. L attivita, se serve, arriva subito dopo.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5 md:grid-cols-2">
            {personalQuestions.map((question) => (
              <QuestionField key={question.key} question={question} register={register} />
            ))}
          </CardContent>
        </Card>
      ) : null}

      {currentStep === 'business_context' ? (
        <Card>
          <CardHeader className="gap-3">
            <div className="flex items-center gap-3">
              <span className="flex size-12 items-center justify-center rounded-2xl bg-violet-50 text-violet-700">
                <BriefcaseBusiness className="size-5" />
              </span>
              <div className="grid gap-1">
                <Badge variant="outline" className="w-fit">Attivita</Badge>
                <CardTitle className="text-2xl">Hai anche un attivita da aggiungere?</CardTitle>
              </div>
            </div>
            <CardDescription className="max-w-3xl text-base leading-7">
              Se hai una partita IVA, una startup o una societa, la aggiungiamo nello stesso profilo. Se non ti serve, vai subito alle prime misure.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5">
            <div className="grid gap-3 md:grid-cols-2">
              <button
                type="button"
                className={modeCardClass(businessMode === 'none')}
                onClick={() => {
                  setBusinessMode('none');
                  setMessage(null);
                }}
              >
                <span className="text-base font-semibold text-slate-950">Non ho attivita</span>
                <span className="text-sm leading-6 text-slate-600">Resto sul profilo personale e passo subito alle prime misure.</span>
              </button>
              <button
                type="button"
                className={modeCardClass(businessMode === 'enabled')}
                onClick={() => {
                  setBusinessMode('enabled');
                  setMessage(null);
                }}
              >
                <span className="text-base font-semibold text-slate-950">Ho o sto aprendo un attivita</span>
                <span className="text-sm leading-6 text-slate-600">Aggiungo un perimetro business nello stesso profilo senza cambiare percorso.</span>
              </button>
            </div>

            {businessMode === 'enabled' ? (
              <div className="grid gap-3 md:grid-cols-3">
                {BUSINESS_TYPE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    className={modeCardClass(selectedBusinessType === option.value)}
                    onClick={() => {
                      setSelectedBusinessType(option.value);
                      setMessage(null);
                    }}
                  >
                    <span className="text-sm font-semibold text-slate-950">{option.label}</span>
                    <span className="text-sm leading-6 text-slate-600">{option.body}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      {currentStep === 'business_core' ? (
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="soft" className="w-fit">Dati attivita</Badge>
            <CardTitle className="text-2xl">Chiudiamo solo le informazioni essenziali.</CardTitle>
            <CardDescription className="max-w-3xl text-base leading-7">
              Queste risposte servono a filtrare le misure per freelance, startup o PMI. Il resto verra solo dopo, se ha davvero senso.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5 md:grid-cols-2">
            {businessQuestions.map((question) => (
              <QuestionField key={question.key} question={question} register={register} />
            ))}
          </CardContent>
        </Card>
      ) : null}

      {currentStep === 'strategic_modules' && currentModule ? (
        <Card>
          <CardHeader className="gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">{currentModule.title}</Badge>
              {currentModule.questions.some((question) => question.sensitive) ? <Badge variant="soft">Solo se serve</Badge> : null}
            </div>
            <CardTitle className="text-2xl">{currentModule.title}</CardTitle>
            <CardDescription className="max-w-3xl text-base leading-7">
              {currentModule.description}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5">
            <div className="rounded-[1.5rem] border border-border/70 bg-slate-50/80 px-5 py-4 text-sm leading-7 text-slate-600">
              {currentModule.why_this_module_matters}
            </div>
            <div className="grid gap-5 md:grid-cols-2">
              {currentModule.questions.map((question) => (
                <QuestionField key={question.key} question={question} register={register} />
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {message ? <div className="banner">{message}</div> : null}

      <div className="flex flex-wrap gap-3">
        {backHref ? (
          <Link className="button-secondary" href={backHref}>
            <ArrowLeft className="size-4" />
            Indietro
          </Link>
        ) : null}

        {(currentStep === 'personal_core' || currentStep === 'business_context' || currentStep === 'business_core' || currentStep === 'strategic_modules') ? (
          <Button
            type="submit"
            className="min-w-[15rem]"
            disabled={isSubmitting || (currentStep === 'business_context' && businessMode === 'enabled' && !selectedBusinessType)}
          >
            {isSubmitting ? 'Salvataggio in corso...' : submitLabel(currentStep, Boolean(currentModule), businessMode)}
          </Button>
        ) : null}

        {currentStep === 'strategic_modules' ? (
          <button type="button" className="button-secondary" onClick={() => window.location.assign(primaryHref)}>
            Salta questo modulo
          </button>
        ) : null}
      </div>
    </form>
  );
}

function QuestionField({
  question,
  register,
}: {
  question: ProfileQuestion;
  register: ReturnType<typeof useForm<FormValues>>['register'];
}) {
  return (
    <div className="grid gap-3 rounded-[1.5rem] border border-border/70 bg-white/85 p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="grid gap-2">
          <Label htmlFor={question.key}>{question.label}</Label>
          {question.helper_text ? <p className="text-sm leading-6 text-slate-600">{question.helper_text}</p> : null}
        </div>
        {question.sensitive ? <Badge variant="outline">Sensibile</Badge> : null}
      </div>

      {question.kind === 'boolean' ? (
        <NativeSelect id={question.key} {...register(question.key)}>
          <option value="">Seleziona</option>
          <option value="true">Si</option>
          <option value="false">No</option>
        </NativeSelect>
      ) : question.options ? (
        <NativeSelect id={question.key} {...register(question.key)}>
          <option value="">Seleziona</option>
          {question.options.map((option) => (
            <option key={option} value={option}>
              {formatOptionLabel(option)}
            </option>
          ))}
        </NativeSelect>
      ) : question.kind === 'text' ? (
        <Textarea id={question.key} {...register(question.key)} />
      ) : question.kind === 'number' ? (
        <Input id={question.key} type="number" {...register(question.key)} />
      ) : (
        <Input id={question.key} {...register(question.key)} />
      )}

      {question.why_needed ? (
        <div className="flex gap-2 rounded-[1.25rem] border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-500">
          <CircleHelp className="mt-0.5 size-4 shrink-0 text-slate-400" />
          <span>{question.sensitive ? 'Perche lo chiediamo adesso: ' : 'Perche lo chiediamo: '}{question.why_needed}</span>
        </div>
      ) : null}
    </div>
  );
}

function buildInitialValues(profile: Profile | null): FormValues {
  const factValues = (profile?.fact_values ?? {}) as Record<string, unknown>;
  const values: FormValues = {};
  Object.entries(factValues).forEach(([key, value]) => {
    if (typeof value === 'boolean') {
      values[key] = value ? 'true' : 'false';
      return;
    }
    values[key] = (value as string | boolean | null) ?? null;
  });
  values.profile_type = (values.profile_type as string | undefined) ?? resolveUserType(profile) ?? 'persona_fisica';
  values.main_operating_region = (values.main_operating_region as string | undefined) ?? profile?.region ?? '';
  values.legal_form_bucket = (values.legal_form_bucket as string | undefined) ?? profile?.legal_entity_type ?? '';
  values.company_age_or_formation_window =
    (values.company_age_or_formation_window as string | undefined) ?? profile?.company_age_band ?? '';
  values.size_band = (values.size_band as string | undefined) ?? profile?.company_size_band ?? '';
  values.sector_macro_category = (values.sector_macro_category as string | undefined) ?? profile?.sector_code_or_category ?? '';
  values.hiring_interest = normalizeBooleanField(values.hiring_interest, profile?.hiring_intent);
  values.export_investment_intent = normalizeBooleanField(values.export_investment_intent, profile?.export_intent);
  values.digital_transition_project = normalizeBooleanField(values.digital_transition_project, profile?.innovation_intent);
  values.energy_transition_project = normalizeBooleanField(values.energy_transition_project, profile?.sustainability_intent);
  return values;
}

function buildPayloadForStep({
  currentStep,
  currentQuestions,
  values,
  businessMode,
  selectedBusinessType,
  profile,
}: {
  currentStep: OnboardingStepKey;
  currentQuestions: ProfileQuestion[];
  values: FormValues;
  businessMode: 'none' | 'enabled';
  selectedBusinessType: string;
  profile: Profile | null;
}) {
  const normalizedFactValues: Record<string, string | boolean | null> = {};
  for (const question of currentQuestions) {
    const normalized = normalizeValue(question, values[question.key]);
    if (normalized !== undefined) {
      normalizedFactValues[question.key] = normalized;
    }
  }

  if (currentStep === 'personal_core') {
    normalizedFactValues.profile_type = resolveBusinessType(profile) ?? 'persona_fisica';
    return { fact_values: normalizedFactValues };
  }

  if (currentStep === 'business_context') {
    if (businessMode === 'enabled') {
      return {
        business_exists: true,
        fact_values: {
          profile_type: selectedBusinessType,
        },
      };
    }
    for (const key of BUSINESS_FACT_KEYS_TO_CLEAR) {
      normalizedFactValues[key] = null;
    }
    normalizedFactValues.profile_type = 'persona_fisica';
    return {
      business_exists: false,
      fact_values: normalizedFactValues,
    };
  }

  normalizedFactValues.profile_type = resolveBusinessType(profile) ?? 'persona_fisica';
  return { fact_values: normalizedFactValues };
}

function normalizeBooleanField(current: string | boolean | null | undefined, fallback: boolean | null | undefined) {
  if (current !== undefined && current !== null && current !== '') return current;
  if (fallback === true) return 'true';
  if (fallback === false) return 'false';
  return null;
}

function normalizeValue(question: ProfileQuestion, value: string | boolean | null | undefined): string | boolean | undefined {
  if (value === '' || value === undefined || value === null) return undefined;
  if (question.kind === 'boolean') {
    if (typeof value === 'boolean') return value;
    return value === 'true';
  }
  return value;
}

function resolveUserType(profile: Profile | null): string | null {
  const factValues = (profile?.fact_values ?? {}) as Record<string, unknown>;
  return (factValues.profile_type as string | undefined) ?? profile?.user_type ?? 'persona_fisica';
}

function resolveBusinessType(profile: Profile | null): string | null {
  const profileType = resolveUserType(profile);
  return profileType && profileType !== 'persona_fisica' ? profileType : null;
}

function computeWizardProgress(payload: ProfileQuestionResponse | null) {
  const visibleSteps = payload?.journey.steps.filter((step) => step.status !== 'locked') ?? [];
  const currentStep = payload?.journey.current_step;
  if (!visibleSteps.length || !currentStep) return 10;
  const index = visibleSteps.findIndex((step) => step.key === currentStep);
  return Math.round(((Math.max(index, 0) + 1) / visibleSteps.length) * 100);
}

function computePrimaryHref(
  step: OnboardingStepKey,
  payload: ProfileQuestionResponse,
  entry?: string,
  businessMode: 'none' | 'enabled' = payload.business_context.enabled ? 'enabled' : 'none',
  returnTo?: string,
): string {
  if (step === 'personal_core') {
    if (returnTo) {
      return returnTo;
    }
    return buildOnboardingHref('business_context', undefined, entry, returnTo);
  }
  if (step === 'business_context') {
    return businessMode === 'enabled'
      ? buildOnboardingHref('business_core', undefined, entry, returnTo)
      : (returnTo ?? buildOnboardingHref('results_checkpoint', undefined, entry, returnTo));
  }
  if (step === 'business_core') {
    if (returnTo) {
      return returnTo;
    }
    return buildOnboardingHref('results_checkpoint', undefined, entry, returnTo);
  }
  if (step === 'results_checkpoint') {
    if (payload.strategic_modules.length) {
      return buildOnboardingHref('strategic_modules', payload.strategic_modules[0]?.key, entry, returnTo);
    }
    return '/' as Route;
  }
  if (step === 'strategic_modules') {
    if (returnTo) {
      return returnTo;
    }
    const currentIndex = payload.strategic_modules.findIndex((module) => module.key === payload.journey.active_module_key);
    const nextModule = payload.strategic_modules[currentIndex + 1];
    if (nextModule) {
      return buildOnboardingHref('strategic_modules', nextModule.key, entry, returnTo);
    }
    return buildOnboardingHref('final_next_actions', undefined, entry, returnTo);
  }
  return '/' as Route;
}

function computeBackHref(step: OnboardingStepKey, payload: ProfileQuestionResponse, entry?: string, returnTo?: string): Route | undefined {
  if (step === 'business_context') {
    if (returnTo) {
      return returnTo as Route;
    }
    return buildOnboardingHref('personal_core', undefined, entry, returnTo);
  }
  if (step === 'business_core') {
    return buildOnboardingHref('business_context', undefined, entry, returnTo);
  }
  if (step === 'results_checkpoint') {
    if (returnTo) {
      return returnTo as Route;
    }
    return buildOnboardingHref(payload.journey.has_business_context ? 'business_core' : 'business_context', undefined, entry, returnTo);
  }
  if (step === 'strategic_modules') {
    if (returnTo) {
      return returnTo as Route;
    }
    const currentIndex = payload.strategic_modules.findIndex((module) => module.key === payload.journey.active_module_key);
    if (currentIndex > 0) {
      return buildOnboardingHref('strategic_modules', payload.strategic_modules[currentIndex - 1]?.key, entry, returnTo);
    }
    return buildOnboardingHref('results_checkpoint', undefined, entry, returnTo);
  }
  if (step === 'final_next_actions') {
    if (returnTo) {
      return returnTo as Route;
    }
    if (payload.strategic_modules.length) {
      return buildOnboardingHref(
        'strategic_modules',
        payload.strategic_modules[payload.strategic_modules.length - 1]?.key,
        entry,
        returnTo,
      );
    }
    return buildOnboardingHref('results_checkpoint', undefined, entry, returnTo);
  }
  return undefined;
}

function buildSearchHref(): Route {
  return '/search' as Route;
}

function submitLabel(step: OnboardingStepKey, hasStrategicModule: boolean, businessMode: 'none' | 'enabled') {
  if (step === 'personal_core') return 'Salva e continua';
  if (step === 'business_context') return businessMode === 'enabled' ? 'Salva e continua' : 'Salva e mostra le prime misure';
  if (step === 'business_core') return 'Salva e mostra le prime misure';
  if (step === 'strategic_modules') return hasStrategicModule ? 'Salva e continua' : 'Vai avanti';
  return 'Salva e continua';
}

function stepCopy(step: OnboardingStepKey, currentModuleTitle?: string) {
  if (step === 'personal_core') {
    return {
      eyebrow: 'Profilo personale',
      title: 'Partiamo da te',
      body: 'Chiudiamo prima le informazioni che spostano davvero misure personali, familiari e parte del matching per eventuali attivita.',
    };
  }
  if (step === 'business_context') {
    return {
      eyebrow: 'Attivita',
      title: 'Decidiamo solo se serve aggiungerla',
      body: 'Qui scegli se restare sul solo profilo personale oppure portare dentro anche una partita IVA, una startup o una PMI.',
    };
  }
  if (step === 'business_core') {
    return {
      eyebrow: 'Dati attivita',
      title: 'Chiudiamo il minimo indispensabile',
      body: 'Bastano poche risposte per filtrare correttamente misure da freelance, startup o impresa.',
    };
  }
  if (step === 'strategic_modules') {
    return {
      eyebrow: currentModuleTitle ?? 'Approfondimenti',
      title: currentModuleTitle ?? 'Domande utili solo se servono',
      body: 'Queste risposte migliorano precisione e conferma dei match, ma non rimettono in discussione il percorso principale.',
    };
  }
  return {
    eyebrow: 'Profilo',
    title: 'Percorso guidato',
    body: 'Continua dal punto giusto per te.',
  };
}

function businessTypeLabel(value: string | null | undefined): string {
  if (!value) return 'Non aggiunta';
  return BUSINESS_TYPE_OPTIONS.find((option) => option.value === value)?.label ?? formatOptionLabel(value);
}

function NarrativeStat({
  label,
  value,
  body,
}: {
  label: string;
  value: string;
  body: string;
}) {
  return (
    <div className="grid gap-3 rounded-[1.5rem] border border-border/70 bg-slate-50/85 p-4 shadow-sm">
      <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</span>
      <p className="font-heading text-2xl font-semibold text-slate-950">{value}</p>
      <p className="text-sm leading-6 text-slate-600">{body}</p>
    </div>
  );
}

function modeCardClass(active: boolean) {
  return [
    'grid gap-2 rounded-[1.5rem] border bg-white px-4 py-4 text-left transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40',
    active
      ? 'border-primary bg-blue-50 text-slate-950 shadow-sm ring-1 ring-primary/20'
      : 'border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50',
  ].join(' ');
}
