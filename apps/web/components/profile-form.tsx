'use client';

import type { Route } from 'next';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { BriefcaseBusiness, ChevronRight, CircleHelp, Sparkles, UserRound } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { NativeSelect } from '@/components/ui/native-select';
import { Textarea } from '@/components/ui/textarea';
import type { Profile, ProfileQuestion, ProfileQuestionResponse } from '@/lib/types';

import { QuestionStepper } from './question-stepper';

const API_URL = '/api/proxy';

type ViewStep = 'core_entity' | 'results' | 'strategic_intent' | 'conditional_accuracy';

type FormValues = Record<string, string | boolean | null>;

const STEP_COPY: Record<ViewStep, { eyebrow: string; title: string; body: string }> = {
  core_entity: {
    eyebrow: 'Step 1',
    title: 'Partiamo dal tuo profilo personale',
    body: 'Chiudiamo prima i dati che contano per te come persona. Se hai gia un attivita o stai per aprirla, aggiungiamo anche quel perimetro nello stesso profilo.',
  },
  results: {
    eyebrow: 'Step 2',
    title: 'Hai gia una prima lettura spendibile',
    body: 'Ora sai gia cosa sta emergendo. Il resto serve a chiudere le ambiguita, non a sbloccare il prodotto.',
  },
  strategic_intent: {
    eyebrow: 'Step 3',
    title: 'Migliora precisione e coverage',
    body: 'Qui apri solo i moduli che corrispondono a progetti reali: assunzioni, export, investimenti digitali o energia.',
  },
  conditional_accuracy: {
    eyebrow: 'Step 4',
    title: 'Chiudi solo i blocchi veri',
    body: 'Le domande finali compaiono solo quando una misura attiva dipende davvero da questa risposta.',
  },
};

const PERSONAL_CORE_PRIMARY_KEYS = [
  'main_operating_region',
  'employment_type',
  'persona_fisica_age_band',
  'family_composition',
  'figli_a_carico_count',
  'isee_bracket',
];

const BUSINESS_CORE_KEYS = [
  'activity_stage',
  'legal_form_bucket',
  'company_age_or_formation_window',
  'size_band',
  'sector_macro_category',
  'innovation_regime_status',
];

const BUSINESS_TYPE_OPTIONS = [
  { value: null, label: 'Solo profilo personale', body: 'Niente partita IVA o impresa da aggiungere per ora.' },
  { value: 'freelancer', label: 'Freelance o partita IVA', body: 'Professionista, autonomo o attivita individuale.' },
  { value: 'startup', label: 'Startup o nuova impresa', body: 'Stai aprendo o hai una realta giovane e in crescita.' },
  { value: 'sme', label: 'PMI o societa attiva', body: 'Hai gia una struttura operativa o una societa avviata.' },
];

const GROUP_LABELS: Record<string, { title: string; body: string }> = {
  hiring: {
    title: 'Assunzioni',
    body: 'Serve solo per incentivi occupazionali e bonus legati al profilo del lavoratore target.',
  },
  export: {
    title: 'Export e mercati',
    body: 'Domande che chiariscono se le famiglie SIMEST e simili sono davvero rilevanti per te.',
  },
  digital_energy: {
    title: 'Digitale, energia e investimenti',
    body: 'Usate per Transizione 4.0 / 5.0 e misure progettuali, non per il matching di base.',
  },
  personal_family: {
    title: 'Benefici personali e familiari',
    body: 'Dati che compaiono solo per misure personali, familiari o fiscali specifiche.',
  },
  general: {
    title: 'Dettagli aggiuntivi',
    body: 'Informazioni ulteriori che possono affinare stato e priorita dei match.',
  },
};
const DEFAULT_GROUP_LABEL = {
  title: 'Dettagli aggiuntivi',
  body: 'Informazioni ulteriori che possono affinare stato e priorita dei match.',
};

const PERSONA_CORE_BRIDGE_QUESTIONS: ProfileQuestion[] = [
  {
    key: 'employment_type',
    label: 'Qual e la tua situazione lavorativa principale?',
    step: 1,
    kind: 'select',
    required: true,
    options: ['dipendente', 'autonomo', 'disoccupato', 'pensionato'],
    helper_text: 'Determina quali famiglie di misure INPS e fiscali si applicano a te.',
    audience: ['persona_fisica'],
    module: 'core_entity',
    sensitive: false,
    depends_on: { profile_type: ['persona_fisica'] },
    ask_when_measure_families: null,
    why_needed: 'NASpI, ANF e regime forfettario dipendono direttamente dal tipo di rapporto lavorativo.',
    coverage_weight: 0,
    ambiguity_reduction_score: 0,
    priority: 100,
    impact_counts: {
      clarification_opportunity_count: 0,
      blocking_opportunity_count: 0,
      upgrade_opportunity_count: 0,
    },
    blocking_opportunity_count: 0,
    upgrade_opportunity_count: 0,
  },
  {
    key: 'persona_fisica_age_band',
    label: "In quale fascia d'eta rientri?",
    step: 1,
    kind: 'select',
    required: true,
    options: ['under_35', '35_55', 'over_55'],
    helper_text: "Alcune misure come il bonus prima casa under 36 e le agevolazioni forfettarie dipendono dall'eta.",
    audience: ['persona_fisica'],
    module: 'core_entity',
    sensitive: false,
    depends_on: { profile_type: ['persona_fisica'] },
    ask_when_measure_families: null,
    why_needed: 'Molti benefici fiscali e contributivi hanno soglie anagrafiche esplicite.',
    coverage_weight: 0,
    ambiguity_reduction_score: 0,
    priority: 95,
    impact_counts: {
      clarification_opportunity_count: 0,
      blocking_opportunity_count: 0,
      upgrade_opportunity_count: 0,
    },
    blocking_opportunity_count: 0,
    upgrade_opportunity_count: 0,
  },
  {
    key: 'family_composition',
    label: "Com'e composto il tuo nucleo familiare?",
    step: 1,
    kind: 'select',
    required: true,
    options: ['single', 'coppia_senza_figli', 'coppia_con_figli', 'genitore_solo_con_figli'],
    helper_text: 'Determina accesso a Assegno Unico, ANF, detrazioni per figli e bonus nido.',
    audience: ['persona_fisica'],
    module: 'core_entity',
    sensitive: false,
    depends_on: { profile_type: ['persona_fisica'] },
    ask_when_measure_families: null,
    why_needed: 'I benefici familiari dipendono dalla composizione del nucleo, non solo dal reddito.',
    coverage_weight: 0,
    ambiguity_reduction_score: 0,
    priority: 90,
    impact_counts: {
      clarification_opportunity_count: 0,
      blocking_opportunity_count: 0,
      upgrade_opportunity_count: 0,
    },
    blocking_opportunity_count: 0,
    upgrade_opportunity_count: 0,
  },
  {
    key: 'figli_a_carico_count',
    label: 'Quanti figli hai a carico?',
    step: 1,
    kind: 'select',
    required: true,
    options: ['0', '1', '2', '3_plus'],
    helper_text: "Il numero di figli cambia l'importo di Assegno Unico, detrazioni e bonus nido.",
    audience: ['persona_fisica'],
    module: 'core_entity',
    sensitive: false,
    depends_on: { profile_type: ['persona_fisica'] },
    ask_when_measure_families: null,
    why_needed: 'Quasi tutte le misure familiari scalano per numero di figli.',
    coverage_weight: 0,
    ambiguity_reduction_score: 0,
    priority: 85,
    impact_counts: {
      clarification_opportunity_count: 0,
      blocking_opportunity_count: 0,
      upgrade_opportunity_count: 0,
    },
    blocking_opportunity_count: 0,
    upgrade_opportunity_count: 0,
  },
  {
    key: 'isee_bracket',
    label: 'Se lo sai gia, in quale fascia ISEE rientra il tuo nucleo?',
    step: 1,
    kind: 'select',
    required: false,
    options: ['under_15k', '15_25k', '25_40k', 'over_40k', 'non_determinato'],
    helper_text: "Non blocca il percorso: se non l'hai sotto mano puoi lasciarlo vuoto e andare avanti.",
    audience: ['persona_fisica'],
    module: 'core_entity',
    sensitive: true,
    depends_on: { profile_type: ['persona_fisica'] },
    ask_when_measure_families: null,
    why_needed: "Molte misure INPS e fiscali hanno soglie ISEE esplicite che cambiano l'importo o l'accesso.",
    coverage_weight: 0,
    ambiguity_reduction_score: 0,
    priority: 70,
    impact_counts: {
      clarification_opportunity_count: 0,
      blocking_opportunity_count: 0,
      upgrade_opportunity_count: 0,
    },
    blocking_opportunity_count: 0,
    upgrade_opportunity_count: 0,
  },
];

const PERSONA_CORE_BRIDGE_ORDER = PERSONA_CORE_BRIDGE_QUESTIONS.map((question) => question.key);

export function ProfileForm({
  profile,
  questionPayload,
  currentStep,
  entry,
}: {
  profile: Profile | null;
  questionPayload: ProfileQuestionResponse | null;
  currentStep: ViewStep;
  entry?: string;
}) {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localStep, setLocalStep] = useState<ViewStep>(currentStep);
  const [selectedBusinessType, setSelectedBusinessType] = useState<string | null>(resolveBusinessType(profile));
  const initialValues = useMemo(() => buildInitialValues(profile), [profile]);
  const { register, handleSubmit, setValue, reset } = useForm<FormValues>({ defaultValues: initialValues });

  useEffect(() => {
    setLocalStep(currentStep);
  }, [currentStep]);

  useEffect(() => {
    setSelectedBusinessType(resolveBusinessType(profile));
  }, [profile]);

  useEffect(() => {
    reset(initialValues);
    setMessage(null);
    setIsSubmitting(false);
  }, [initialValues, reset]);

  const activeStep = localStep;
  const activeProfileTypes = useMemo(
    () => buildActiveProfileTypes(selectedBusinessType),
    [selectedBusinessType]
  );
  const moduleMap = useMemo(() => new Map((questionPayload?.modules ?? []).map((module) => [module.key, module])), [questionPayload]);
  const activeQuestions = useMemo(() => {
    if (activeStep === 'results') return [];
    const rawQuestions = moduleMap.get(activeStep)?.questions ?? [];
    if (activeStep !== 'core_entity') {
      return rawQuestions.filter((question) => questionMatchesContexts(question, activeProfileTypes));
    }

    const rawQuestionsByKey = new Map(rawQuestions.map((question) => [question.key, question]));
    const questionsByKey = new Map<string, ProfileQuestion>();
    for (const question of rawQuestions) {
      if (question.key === 'profile_type') continue;
      if (BUSINESS_CORE_KEYS.includes(question.key) && !selectedBusinessType) continue;
      if (!questionMatchesContexts(question, activeProfileTypes)) continue;
      questionsByKey.set(question.key, prepareQuestion(question));
    }
    for (const key of PERSONAL_CORE_PRIMARY_KEYS) {
      const existing =
        questionsByKey.get(key) ??
        (rawQuestionsByKey.get(key) ? prepareQuestion(rawQuestionsByKey.get(key) as ProfileQuestion) : undefined) ??
        PERSONA_CORE_BRIDGE_QUESTIONS.find((question) => question.key === key);
      if (existing) {
        questionsByKey.set(key, existing);
      }
    }
    return Array.from(questionsByKey.values()).sort((left, right) => coreQuestionOrder(left.key) - coreQuestionOrder(right.key));
  }, [activeProfileTypes, activeStep, moduleMap, selectedBusinessType]);
  const personalCoreQuestions = useMemo(
    () => activeQuestions.filter((question) => PERSONAL_CORE_PRIMARY_KEYS.includes(question.key)),
    [activeQuestions]
  );
  const businessCoreQuestions = useMemo(
    () => activeQuestions.filter((question) => BUSINESS_CORE_KEYS.includes(question.key)),
    [activeQuestions]
  );
  const groupedQuestions = useMemo(() => groupQuestionsByIntent(activeQuestions), [activeQuestions]);
  const hasConditionalQuestions = Boolean((moduleMap.get('conditional_accuracy')?.questions ?? []).length);
  const progress = questionPayload?.progress_summary;
  const progressPercent = progress ? Math.min(100, Math.max(8, progress.completeness_score)) : 8;

  if (activeStep === 'results') {
    return (
      <div className="grid gap-6">
        <QuestionStepper current="results" progress={progressPercent} hrefForStep={(stepKey) => hrefForStep(stepKey, entry, hasConditionalQuestions)} />
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="soft" className="w-fit">{STEP_COPY.results.eyebrow}</Badge>
            <CardTitle className="text-4xl leading-[0.95]">{STEP_COPY.results.title}</CardTitle>
            <CardDescription className="max-w-2xl text-base leading-7">{STEP_COPY.results.body}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
            <div className="grid gap-4 rounded-[1.75rem] border border-border/70 bg-white/80 p-5">
              <div className="flex items-center gap-2 text-primary">
                <Sparkles className="size-4" />
                <span className="text-sm font-semibold">Il motore ha gia un perimetro serio.</span>
              </div>
              <p className="text-sm leading-7 text-slate-600">
                Da qui in poi scegli tu quanta precisione aggiungere. Le domande successive servono solo a chiarire i casi ancora aperti, non a sbloccare il prodotto.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link className="button" href={nextHref('results', hasConditionalQuestions, entry) as Route}>
                  Migliora precisione
                  <ChevronRight className="size-4" />
                </Link>
                <Link className="button-secondary" href={`/search${entry ? `?entry=${encodeURIComponent(entry)}` : ''}` as Route}>
                  Vai ai risultati completi
                </Link>
              </div>
            </div>
            <div className="grid gap-3 rounded-[1.75rem] border border-border/70 bg-slate-50/85 p-5 text-sm text-slate-600">
              <span className="eyebrow">Stato attuale</span>
              <span>Core salvato: {progress?.core_answered ?? 0}/{progress?.core_total ?? 0}</span>
              <span>Ora puoi vedere i risultati o continuare solo con le risposte piu utili.</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const copy = getStepCopy(activeStep);

  return (
    <form
      className="grid gap-6"
      onSubmit={handleSubmit(async (values) => {
        setMessage(null);
        setIsSubmitting(true);
        const currentQuestions = activeQuestions;
        const normalizedFactValues: Record<string, string | boolean | null> = Object.fromEntries(
          currentQuestions
            .map((question) => [question.key, normalizeValue(question, values[question.key])])
            .filter(([, value]) => value !== undefined)
        );
        normalizedFactValues.profile_type = selectedBusinessType ?? 'persona_fisica';
        if (!selectedBusinessType) {
          for (const key of BUSINESS_FACT_KEYS_TO_CLEAR) {
            normalizedFactValues[key] = null;
          }
        }
        const response = await fetch(`${API_URL}/v1/profile`, {
          method: 'PUT',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ fact_values: normalizedFactValues }),
        });
        if (!response.ok) {
          setMessage('Aggiornamento non riuscito. Riprova tra qualche secondo.');
          setIsSubmitting(false);
          return;
        }
        setIsSubmitting(false);
        router.push(nextHref(activeStep, hasConditionalQuestions, entry) as Route);
      })}
    >
      <QuestionStepper current={activeStep} progress={progressPercent} hrefForStep={(stepKey) => hrefForStep(stepKey, entry, hasConditionalQuestions)} />

      <Card>
        <CardHeader className="gap-3">
          <Badge variant="soft" className="w-fit">{copy.eyebrow}</Badge>
          <CardTitle className="text-4xl leading-[0.95]">{copy.title}</CardTitle>
          <CardDescription className="max-w-3xl text-base leading-7">{copy.body}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <NarrativeStat
            label="Profilo personale"
            value="Sempre attivo"
            body="Ogni match parte da te: lavoro, fascia di eta, regione e nucleo possono cambiare l'esito."
          />
          <NarrativeStat
            label="Questo step"
            value={activeQuestions.length > 0 ? `${activeQuestions.length} risposte utili` : 'Niente da aggiungere'}
            body={activeQuestions.length > 0 ? 'Ti chiediamo solo il minimo che cambia davvero la lettura dei risultati.' : 'Puoi passare oltre senza perdere contesto.'}
          />
          <NarrativeStat
            label="Attivita"
            value={selectedBusinessType ? businessTypeLabel(selectedBusinessType) : 'Non aggiunta'}
            body={selectedBusinessType ? 'Il feed terra insieme opportunita personali e per la tua attivita.' : 'Se serve, la aggiungi qui senza cambiare percorso.'}
          />
        </CardContent>
      </Card>

      {activeStep === 'core_entity' ? (
        <>
          <Card>
            <CardHeader className="gap-3">
              <div className="flex items-center gap-3">
                <span className="flex size-12 items-center justify-center rounded-2xl bg-blue-50 text-primary">
                  <UserRound className="size-5" />
                </span>
                <div className="grid gap-1">
                  <Badge variant="outline" className="w-fit">Profilo personale</Badge>
                  <CardTitle className="text-2xl">Questa parte vale per tutti</CardTitle>
                </div>
              </div>
              <CardDescription className="max-w-3xl text-base leading-7">
                Prima raccogliamo i dati che possono cambiare bonus personali, familiari, lavoro e anche parte dei match per attivita. La tua regione principale resta qui dentro, cosi il feed parte comunque da te.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5 md:grid-cols-2">
              {personalCoreQuestions.map((question) => (
                <QuestionField key={question.key} question={question} register={register} />
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="gap-3">
              <div className="flex items-center gap-3">
                <span className="flex size-12 items-center justify-center rounded-2xl bg-violet-50 text-violet-700">
                  <BriefcaseBusiness className="size-5" />
                </span>
                <div className="grid gap-1">
                  <Badge variant="soft" className="w-fit">Attivita opzionale</Badge>
                  <CardTitle className="text-2xl">Aggiungi anche la tua attivita, se esiste</CardTitle>
                </div>
              </div>
              <CardDescription className="max-w-3xl text-base leading-7">
                Se hai una partita IVA, una startup o una PMI, il feed puo tenere insieme opportunita personali e per impresa. Se non ti serve, lasci tutto sul solo profilo personale.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                {BUSINESS_TYPE_OPTIONS.map((option) => (
                  <button
                    key={option.label}
                    type="button"
                    className={profileModeCardClass(selectedBusinessType === option.value)}
                    disabled={isSubmitting}
                    onClick={() => switchBusinessType(option.value, setSelectedBusinessType, setValue, setMessage)}
                  >
                    <span className="text-sm font-semibold text-slate-950">{option.label}</span>
                    <span className="text-sm leading-6 text-slate-600">{option.body}</span>
                  </button>
                ))}
              </div>
              {selectedBusinessType ? (
                <>
                  <div className="rounded-[1.5rem] border border-violet-100 bg-violet-50/80 px-5 py-4 text-sm leading-7 text-violet-950">
                    Hai aggiunto <strong>{businessTypeLabel(selectedBusinessType)}</strong>. Ora chiudiamo solo i dati d impresa che spostano davvero l ammissibilita iniziale.
                  </div>
                  {businessCoreQuestions.length > 0 ? (
                    <div className="grid gap-5 md:grid-cols-2">
                      {businessCoreQuestions.map((question) => (
                        <QuestionField key={question.key} question={question} register={register} />
                      ))}
                    </div>
                  ) : null}
                </>
              ) : (
                <div className="rounded-[1.5rem] border border-border/70 bg-slate-50/80 px-5 py-4 text-sm leading-7 text-slate-600">
                  Nessuna attivita aggiunta per ora. Vai avanti con il tuo profilo personale e, se ti serve, torna qui quando vuoi.
                </div>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}

      {activeStep !== 'core_entity'
        ? groupedQuestions.map(([groupKey, questions]) => {
        const groupMeta = GROUP_LABELS[groupKey] ?? DEFAULT_GROUP_LABEL;
        return (
          <Card key={groupKey}>
            <CardHeader className="gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{groupMeta.title}</Badge>
                {questions.some((question) => question.sensitive) ? <Badge variant="soft">Sensibile solo se serve</Badge> : null}
              </div>
              <CardTitle className="text-2xl">{groupMeta.title}</CardTitle>
              <CardDescription>{groupMeta.body}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5 md:grid-cols-2">
              {questions.map((question) => (
                <QuestionField key={question.key} question={question} register={register} />
              ))}
            </CardContent>
          </Card>
        );
        })
        : null}

      {activeQuestions.length === 0 ? (
        <Card>
          <CardContent className="grid gap-3 py-8 text-sm text-slate-600">
            <p className="font-medium text-slate-900">Qui non c e altro che cambi davvero i risultati.</p>
            <p>Puoi andare avanti: i match sono gia leggibili e le prossime domande compaiono solo quando stringono casi ancora aperti.</p>
          </CardContent>
        </Card>
      ) : null}

      <div className="flex flex-wrap gap-3">
        <Button type="submit" className="min-w-[16rem]" disabled={isSubmitting}>
          {isSubmitting ? 'Salvataggio e ricalcolo...' : submitLabel(activeStep, hasConditionalQuestions)}
        </Button>
        {activeStep !== 'core_entity' ? (
          <Link className="button-secondary" href={skipHref(entry) as Route}>
            Salta per ora
          </Link>
        ) : null}
      </div>
      {message ? <div className="banner">{message}</div> : null}
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
        <div className="flex flex-wrap gap-2">
          {question.sensitive ? <Badge variant="outline">Sensibile</Badge> : null}
        </div>
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

      <div className="grid gap-2 text-sm text-slate-500">
        {question.why_needed ? (
          <div className="flex gap-2 rounded-[1.25rem] border border-slate-200 bg-slate-50/80 px-4 py-3">
            <CircleHelp className="mt-0.5 size-4 shrink-0 text-slate-400" />
            <span>{question.sensitive ? 'Perche lo chiediamo adesso: ' : 'Perche lo chiediamo: '}{question.why_needed}</span>
          </div>
        ) : null}
      </div>
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

function formatOptionLabel(option: string): string {
  return option.replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function resolveUserType(profile: Profile | null): string | null {
  const factValues = (profile?.fact_values ?? {}) as Record<string, unknown>;
  return (factValues.profile_type as string | undefined) ?? profile?.user_type ?? 'persona_fisica';
}

function resolveBusinessType(profile: Profile | null): string | null {
  const profileType = resolveUserType(profile);
  return profileType && profileType !== 'persona_fisica' ? profileType : null;
}

function buildActiveProfileTypes(businessType: string | null): string[] {
  return businessType ? ['persona_fisica', businessType] : ['persona_fisica'];
}

function groupQuestionsByIntent(questions: ProfileQuestion[]): [string, ProfileQuestion[]][] {
  const buckets = new Map<string, ProfileQuestion[]>();
  for (const question of questions) {
    const key = questionGroupKey(question.key);
    const bucket = buckets.get(key) ?? [];
    bucket.push(question);
    buckets.set(key, bucket);
  }
  return Array.from(buckets.entries()).sort((left, right) => left[0].localeCompare(right[0]));
}

function prepareQuestion(question: ProfileQuestion): ProfileQuestion {
  if (question.key !== 'main_operating_region') return question;
  return {
    ...question,
    label: 'Qual e la tua regione principale?',
    helper_text:
      'Usiamo una sola regione di riferimento per partire. Ci aiuta subito sia sui benefici personali sia sulle misure legate alla tua attivita.',
    why_needed:
      'Molte opportunita dipendono da dove vivi o operi principalmente. Per ora la usiamo come riferimento unico per tenere il percorso semplice.',
  };
}

function questionGroupKey(key: string): string {
  if (key.startsWith('target_hire_') || key === 'hiring_interest') return 'hiring';
  if (key.includes('export') || key.includes('market')) return 'export';
  if (key.includes('digital') || key.includes('energy') || key.includes('patent') || key.includes('balance')) return 'digital_energy';
  if (key.includes('family') || key.includes('isee') || key.includes('figli') || key.includes('persona_fisica') || key.includes('home_ownership') || key.includes('employment')) {
    return 'personal_family';
  }
  return 'general';
}

function coreQuestionOrder(key: string): number {
  const personalIndex = PERSONAL_CORE_PRIMARY_KEYS.indexOf(key);
  if (personalIndex !== -1) return personalIndex;
  const businessIndex = BUSINESS_CORE_KEYS.indexOf(key);
  if (businessIndex !== -1) return PERSONAL_CORE_PRIMARY_KEYS.length + businessIndex + 10;
  const personaBridgeIndex = PERSONA_CORE_BRIDGE_ORDER.indexOf(key);
  return personaBridgeIndex === -1 ? 999 : PERSONAL_CORE_PRIMARY_KEYS.length + BUSINESS_CORE_KEYS.length + personaBridgeIndex + 20;
}

function getStepCopy(step: ViewStep) {
  return STEP_COPY[step];
}

function hrefForStep(
  stepKey: string,
  entry: string | undefined,
  hasConditionalQuestions: boolean
): Route | null {
  if (stepKey === 'core_entity') return buildOnboardingHref(undefined, entry);
  if (stepKey === 'results') return buildOnboardingHref('results', entry);
  if (stepKey === 'strategic_intent') return buildOnboardingHref('strategic', entry);
  if (stepKey === 'conditional_accuracy') return hasConditionalQuestions ? buildOnboardingHref('conditional', entry) : null;
  return null;
}

function buildOnboardingHref(step: 'results' | 'strategic' | 'conditional' | undefined, entry?: string): Route {
  const search = new URLSearchParams();
  if (step) search.set('step', step);
  if (entry) search.set('entry', entry);
  const suffix = search.toString();
  return (`/onboarding${suffix ? `?${suffix}` : ''}`) as Route;
}

function switchBusinessType(
  nextType: string | null,
  setSelectedBusinessType: (value: string | null) => void,
  setValue: ReturnType<typeof useForm<FormValues>>['setValue'],
  setMessage: (value: string | null) => void
) {
  setSelectedBusinessType(nextType);
  setValue('profile_type', nextType ?? 'persona_fisica');
  setMessage(null);
}

function submitLabel(step: ViewStep, hasConditionalQuestions: boolean): string {
  if (step === 'core_entity') return 'Salva il core e mostra i risultati';
  if (step === 'strategic_intent') return hasConditionalQuestions ? 'Salva e passa alla chiusura finale' : 'Salva e vai ai risultati';
  return 'Aggiorna e vai ai risultati';
}

function nextHref(step: ViewStep, hasConditionalQuestions: boolean, entry?: string): string {
  const suffix = entry ? `?entry=${encodeURIComponent(entry)}` : '';
  if (step === 'core_entity') return `/onboarding?step=results${entry ? `&entry=${encodeURIComponent(entry)}` : ''}`;
  if (step === 'results') return `/onboarding?step=strategic${entry ? `&entry=${encodeURIComponent(entry)}` : ''}`;
  if (step === 'strategic_intent' && hasConditionalQuestions) return `/onboarding?step=conditional${entry ? `&entry=${encodeURIComponent(entry)}` : ''}`;
  return `/search${suffix}`;
}

function skipHref(entry?: string): string {
  return `/search${entry ? `?entry=${encodeURIComponent(entry)}` : ''}`;
}

function questionMatchesContexts(question: ProfileQuestion, activeProfileTypes: string[]): boolean {
  if (!question.audience || question.audience.length === 0) return true;
  return question.audience.some((audience) => activeProfileTypes.includes(audience));
}

function businessTypeLabel(value: string): string {
  if (value === 'freelancer') return 'Freelance o partita IVA';
  if (value === 'startup') return 'Startup o nuova impresa';
  if (value === 'sme') return 'PMI o societa attiva';
  return formatOptionLabel(value);
}

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

function NarrativeStat({ label, value, body }: { label: string; value: string; body: string }) {
  return (
    <div className="rounded-[1.5rem] border border-border/70 bg-slate-50/85 p-4 shadow-sm">
      <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</span>
      <p className="mt-2 font-heading text-2xl font-semibold text-slate-950">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
    </div>
  );
}

function profileModeCardClass(active: boolean) {
  return [
    'grid gap-2 rounded-[1.5rem] border bg-white px-4 py-4 text-left transition-all duration-200',
    active
      ? 'border-primary bg-blue-50 text-slate-900 shadow-sm'
      : 'border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50',
  ].join(' ');
}
