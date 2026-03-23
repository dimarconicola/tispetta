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

type ViewStep = 'gate' | 'core_entity' | 'results' | 'strategic_intent' | 'conditional_accuracy';

type FormValues = Record<string, string | boolean | null>;

const STEP_COPY: Record<Exclude<ViewStep, 'gate'>, { eyebrow: string; title: string; body: string }> = {
  core_entity: {
    eyebrow: 'Step 1',
    title: 'Chiudi il perimetro stabile',
    body: "Compila solo i dati che spostano davvero l'ammissibilita iniziale. Dopo il salvataggio vedi subito i primi match.",
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
  const [selectedProfileType, setSelectedProfileType] = useState<string | null>(resolveUserType(profile));
  const initialValues = useMemo(() => buildInitialValues(profile), [profile]);
  const { register, handleSubmit, watch, setValue, reset } = useForm<FormValues>({ defaultValues: initialValues });

  useEffect(() => {
    setLocalStep(currentStep);
  }, [currentStep]);

  useEffect(() => {
    setSelectedProfileType(resolveUserType(profile));
  }, [profile]);

  useEffect(() => {
    reset(initialValues);
    setMessage(null);
    setIsSubmitting(false);
  }, [initialValues, reset]);

  const activeStep = localStep === 'gate' && selectedProfileType ? 'core_entity' : localStep;
  const watchedProfileType = (watch('profile_type') as string | undefined) || selectedProfileType || 'startup';
  const moduleMap = useMemo(() => new Map((questionPayload?.modules ?? []).map((module) => [module.key, module])), [questionPayload]);
  const activeQuestions = useMemo(() => {
    if (activeStep === 'results' || activeStep === 'gate') return [];
    const rawQuestions = moduleMap.get(activeStep)?.questions ?? [];
    const filteredQuestions = rawQuestions
      .filter((question) => !question.audience || question.audience.includes(watchedProfileType))
      .filter((question) => !(activeStep === 'core_entity' && question.key === 'profile_type'));
    if (activeStep !== 'core_entity' || watchedProfileType !== 'persona_fisica') {
      return filteredQuestions;
    }
    const questionsByKey = new Map(filteredQuestions.map((question) => [question.key, question]));
    PERSONA_CORE_BRIDGE_QUESTIONS.forEach((question) => {
      if (!questionsByKey.has(question.key)) {
        questionsByKey.set(question.key, question);
      }
    });
    return Array.from(questionsByKey.values()).sort((left, right) => personaQuestionOrder(left.key) - personaQuestionOrder(right.key));
  }, [activeStep, moduleMap, watchedProfileType]);
  const groupedQuestions = useMemo(() => groupQuestionsByIntent(activeQuestions), [activeQuestions]);
  const hasConditionalQuestions = Boolean((moduleMap.get('conditional_accuracy')?.questions ?? []).length);
  const progress = questionPayload?.progress_summary;
  const progressPercent = progress ? Math.min(100, Math.max(8, progress.completeness_score)) : 8;

  if (activeStep === 'gate' && !selectedProfileType) {
    return (
      <div className="grid gap-6">
        <QuestionStepper current="gate" progress={6} hrefForStep={(stepKey) => hrefForStep(stepKey, entry, selectedProfileType, hasConditionalQuestions)} />
        <Card>
          <CardHeader className="gap-3">
            <Badge variant="soft" className="w-fit">Step 0</Badge>
            <CardTitle className="text-4xl leading-[0.95]">Per chi stai cercando opportunita?</CardTitle>
            <CardDescription className="max-w-2xl text-base leading-7">
              Questa scelta non e cosmetica: separa benefici personali e familiari dalle misure per attivita, freelance, startup e PMI.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <button
              type="button"
              className={gateCardClass}
              disabled={isSubmitting}
              onClick={() => {
                setSelectedProfileType('persona_fisica');
                setValue('profile_type', 'persona_fisica');
                setLocalStep('core_entity');
                setMessage(null);
              }}
            >
              <div className="flex items-center gap-3">
                <span className="flex size-12 items-center justify-center rounded-2xl bg-blue-50 text-primary">
                  <UserRound className="size-5" />
                </span>
                <div className="text-left">
                  <p className="text-base font-semibold text-slate-950">Persona fisica</p>
                  <p className="mt-1 text-sm text-slate-600">Bonus familiari, INPS, fisco personale, lavoro e casa.</p>
                </div>
              </div>
              <span className="text-sm font-medium text-slate-500">Percorso breve e focalizzato sui tuoi diritti personali.</span>
            </button>

            <button
              type="button"
              className={gateCardClass}
              disabled={isSubmitting}
              onClick={() => {
                setSelectedProfileType('startup');
                setValue('profile_type', 'startup');
                setLocalStep('core_entity');
                setMessage(null);
              }}
            >
              <div className="flex items-center gap-3">
                <span className="flex size-12 items-center justify-center rounded-2xl bg-violet-50 text-violet-700">
                  <BriefcaseBusiness className="size-5" />
                </span>
                <div className="text-left">
                  <p className="text-base font-semibold text-slate-950">Attivita o impresa</p>
                  <p className="mt-1 text-sm text-slate-600">Freelance, startup, PMI, crediti, voucher, export, assunzioni.</p>
                </div>
              </div>
              <span className="text-sm font-medium text-slate-500">Prima ti chiediamo perimetro stabile, poi solo i moduli che servono davvero.</span>
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (activeStep === 'results') {
    return (
      <div className="grid gap-6">
        <QuestionStepper current="results" progress={progressPercent} hrefForStep={(stepKey) => hrefForStep(stepKey, entry, selectedProfileType, hasConditionalQuestions)} />
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

  const copy = getStepCopy(activeStep as Exclude<ViewStep, 'gate'>, selectedProfileType);

  return (
    <form
      className="grid gap-6"
      onSubmit={handleSubmit(async (values) => {
        setMessage(null);
        setIsSubmitting(true);
        const currentQuestions = activeQuestions;
        const normalizedFactValues = Object.fromEntries(
          currentQuestions
            .map((question) => [question.key, normalizeValue(question, values[question.key])])
            .filter(([, value]) => value !== undefined)
        );
        if (!normalizedFactValues.profile_type && selectedProfileType) {
          normalizedFactValues.profile_type = selectedProfileType;
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
        router.push(nextHref(activeStep, hasConditionalQuestions, entry) as Route);
      })}
    >
      <QuestionStepper current={activeStep} progress={progressPercent} hrefForStep={(stepKey) => hrefForStep(stepKey, entry, selectedProfileType, hasConditionalQuestions)} />

      <Card>
        <CardHeader className="gap-3">
          <Badge variant="soft" className="w-fit">{copy.eyebrow}</Badge>
          <CardTitle className="text-4xl leading-[0.95]">{copy.title}</CardTitle>
          <CardDescription className="max-w-3xl text-base leading-7">{copy.body}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <NarrativeStat
            label="Percorso"
            value={selectedProfileType === 'persona_fisica' ? 'Persona fisica' : 'Attivita o impresa'}
            body={selectedProfileType === 'persona_fisica' ? 'Bonus personali, familiari e lavoro.' : 'Freelance, startup, PMI, crediti e incentivi.'}
          />
          <NarrativeStat
            label="Questo step"
            value={activeQuestions.length > 0 ? `${activeQuestions.length} risposte utili` : 'Niente da aggiungere'}
            body={activeQuestions.length > 0 ? 'Ti chiediamo solo il minimo che cambia davvero la lettura dei risultati.' : 'Puoi passare oltre senza perdere contesto.'}
          />
          <NarrativeStat
            label="Poi"
            value={nextStepLabel(activeStep, hasConditionalQuestions)}
            body="Dopo il salvataggio resti nel flusso e puoi sempre tornare ai passaggi gia chiusi."
          />
        </CardContent>
      </Card>

      {activeStep === 'core_entity' ? (
        <Card>
          <CardContent className="grid gap-4 py-5">
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className={profileModeButtonClass(selectedProfileType === 'persona_fisica')}
                disabled={isSubmitting}
                onClick={() => switchProfileType('persona_fisica', setSelectedProfileType, setValue, setLocalStep, setMessage)}
              >
                Persona fisica
              </button>
              <button
                type="button"
                className={profileModeButtonClass(selectedProfileType !== 'persona_fisica')}
                disabled={isSubmitting}
                onClick={() => switchProfileType('startup', setSelectedProfileType, setValue, setLocalStep, setMessage)}
              >
                Attivita o impresa
              </button>
            </div>
            <div className="rounded-[1.5rem] border border-blue-100 bg-blue-50/80 px-5 py-4 text-sm leading-7 text-blue-950">
              {selectedProfileType === 'persona_fisica' ? (
                <>
                  Hai scelto il percorso <strong>Persona fisica</strong>. Qui chiudiamo subito lavoro, eta, nucleo e figli a carico. Se sai gia la fascia ISEE, aggiungila ora: migliora la precisione, ma non ti blocca.
                </>
              ) : (
                <>
                  Hai scelto il percorso <strong>Attivita o impresa</strong>. Qui chiudiamo il perimetro stabile che sposta davvero l ammissibilita iniziale: fase, forma, territorio, dimensione, settore e regime innovativo.
                </>
              )}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {groupedQuestions.map(([groupKey, questions]) => {
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
      })}

      {activeQuestions.length === 0 ? (
        <Card>
          <CardContent className="grid gap-3 py-8 text-sm text-slate-600">
            <p className="font-medium text-slate-900">Per questo step non c e altro che sposti davvero i match.</p>
            <p>Puoi andare avanti: i risultati sono gia leggibili e le prossime domande compariranno solo se chiariscono opportunita vive.</p>
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
  values.profile_type = (values.profile_type as string | undefined) ?? resolveUserType(profile) ?? '';
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
  return (factValues.profile_type as string | undefined) ?? profile?.user_type ?? null;
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

function questionGroupKey(key: string): string {
  if (key.startsWith('target_hire_') || key === 'hiring_interest') return 'hiring';
  if (key.includes('export') || key.includes('market')) return 'export';
  if (key.includes('digital') || key.includes('energy') || key.includes('patent') || key.includes('balance')) return 'digital_energy';
  if (key.includes('family') || key.includes('isee') || key.includes('figli') || key.includes('persona_fisica') || key.includes('home_ownership') || key.includes('employment')) {
    return 'personal_family';
  }
  return 'general';
}

function personaQuestionOrder(key: string): number {
  const index = PERSONA_CORE_BRIDGE_ORDER.indexOf(key);
  return index === -1 ? PERSONA_CORE_BRIDGE_ORDER.length + 100 : index;
}

function getStepCopy(step: Exclude<ViewStep, 'gate'>, profileType: string | null) {
  if (step === 'core_entity' && profileType === 'persona_fisica') {
    return {
      eyebrow: 'Step 1',
      title: 'Chiudi il perimetro personale che sposta davvero i bonus',
      body: 'Partiamo da lavoro, fascia di eta, nucleo e figli a carico. Se conosci gia l ISEE, aggiungilo adesso: migliora subito i match familiari e reddituali, ma non ti blocca.',
    };
  }

  return STEP_COPY[step];
}

function hrefForStep(
  stepKey: string,
  entry: string | undefined,
  profileType: string | null,
  hasConditionalQuestions: boolean
): Route | null {
  if (stepKey === 'gate') return profileType ? null : buildOnboardingHref(undefined, entry);
  if (!profileType) return null;
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

function nextStepLabel(step: ViewStep, hasConditionalQuestions: boolean) {
  if (step === 'core_entity') return 'Prime opportunita';
  if (step === 'results') return 'Precisione facoltativa';
  if (step === 'strategic_intent') return hasConditionalQuestions ? 'Chiusura finale' : 'Catalogo e shortlist';
  return 'Catalogo e shortlist';
}

function switchProfileType(
  nextType: string,
  setSelectedProfileType: (value: string | null) => void,
  setValue: ReturnType<typeof useForm<FormValues>>['setValue'],
  setLocalStep: (value: ViewStep) => void,
  setMessage: (value: string | null) => void
) {
  setSelectedProfileType(nextType);
  setValue('profile_type', nextType);
  setLocalStep('core_entity');
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

function NarrativeStat({ label, value, body }: { label: string; value: string; body: string }) {
  return (
    <div className="rounded-[1.5rem] border border-border/70 bg-slate-50/85 p-4 shadow-sm">
      <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</span>
      <p className="mt-2 font-heading text-2xl font-semibold text-slate-950">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
    </div>
  );
}

const gateCardClass =
  'grid gap-4 rounded-[1.75rem] border border-slate-200 bg-white p-5 text-left shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-slate-300 hover:shadow-lg';

function profileModeButtonClass(active: boolean) {
  return [
    'inline-flex min-h-11 items-center justify-center rounded-full border px-4 text-sm font-medium transition-all duration-200',
    active
      ? 'border-primary bg-primary text-primary-foreground shadow-sm'
      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50',
  ].join(' ');
}
