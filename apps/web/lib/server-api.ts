import { cookies } from 'next/headers';

import { INTERNAL_API_URL, SESSION_COOKIE_NAME } from '@/lib/env';
import type {
  ApiHealthSummary,
  AdminDocument,
  AdminIntegritySnapshot,
  BootstrapRunResult,
  IngestionRun,
  IngestionRunDetail,
  MeasureFamily,
  NotificationHistoryItem,
  NotificationPreferences,
  OpportunityCard,
  OpportunityDetail,
  Profile,
  ProfileQuestionResponse,
  ReviewItem,
  RuleListItem,
  RuleTestResult,
  SessionUser,
  Source,
  SurveyCoverageSnapshot,
} from './types';

const API_TIMEOUT_MS = 10_000;

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  const cookieStore = await cookies();
  const session = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const response = await fetch(`${INTERNAL_API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(session ? { 'X-Session-Token': session } : {}),
      ...(init?.headers ?? {}),
    },
    signal: init?.signal ?? AbortSignal.timeout(API_TIMEOUT_MS),
    cache: 'no-store',
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getApiHealthSummary(): Promise<ApiHealthSummary | null> {
  try {
    const response = await fetch(`${INTERNAL_API_URL}/health`, {
      cache: 'force-cache',
      next: { revalidate: 60 },
      signal: AbortSignal.timeout(2_500),
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as ApiHealthSummary;
  } catch {
    return null;
  }
}

export async function getSessionUser(): Promise<SessionUser | null> {
  return apiFetch<SessionUser>('/v1/me');
}

export async function getProfile(): Promise<Profile | null> {
  return apiFetch<Profile>('/v1/profile');
}

export async function getProfileQuestions(params?: { step?: string; module?: string }): Promise<ProfileQuestionResponse | null> {
  const search = new URLSearchParams();
  if (params?.step) {
    search.set('step', params.step);
  }
  if (params?.module) {
    search.set('module', params.module);
  }
  return apiFetch<ProfileQuestionResponse>(`/v1/profile/questions${search.toString() ? `?${search.toString()}` : ''}`);
}

export async function getOpportunities(params?: Record<string, string | boolean | undefined>): Promise<OpportunityCard[]> {
  const search = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      search.set(key, String(value));
    }
  });
  const path = `/v1/opportunities${search.toString() ? `?${search.toString()}` : ''}`;
  return (await apiFetch<OpportunityCard[]>(path)) ?? [];
}

export async function getOpportunityDetail(key: string): Promise<OpportunityDetail | null> {
  return apiFetch<OpportunityDetail>(`/v1/opportunities/${key}`);
}

export async function searchOpportunities(query: string, scope?: string): Promise<OpportunityCard[]> {
  const search = new URLSearchParams({ query });
  if (scope) {
    search.set('scope', scope);
  }
  return (await apiFetch<OpportunityCard[]>(`/v1/search?${search.toString()}`)) ?? [];
}

export async function getNotificationPreferences(): Promise<NotificationPreferences | null> {
  return apiFetch<NotificationPreferences>('/v1/notifications/preferences');
}

export async function getNotificationHistory(): Promise<NotificationHistoryItem[]> {
  return (await apiFetch<NotificationHistoryItem[]>('/v1/notifications/history')) ?? [];
}

export async function getAdminSources(): Promise<Source[]> {
  return (await apiFetch<Source[]>('/v1/admin/sources')) ?? [];
}

export async function getAdminMeasureFamilies(): Promise<MeasureFamily[]> {
  return (await apiFetch<MeasureFamily[]>('/v1/admin/measure-families')) ?? [];
}

export async function getAdminDocuments(params?: Record<string, string | undefined>): Promise<AdminDocument[]> {
  const search = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value) {
      search.set(key, value);
    }
  });
  const path = `/v1/admin/documents${search.toString() ? `?${search.toString()}` : ''}`;
  return (await apiFetch<AdminDocument[]>(path)) ?? [];
}

export async function getAdminIngestionRun(id: string): Promise<IngestionRunDetail | null> {
  return apiFetch<IngestionRunDetail>(`/v1/admin/ingestion-runs/${id}`);
}

export async function getAdminSurveyCoverage(): Promise<SurveyCoverageSnapshot | null> {
  return apiFetch<SurveyCoverageSnapshot>('/v1/admin/survey/coverage');
}

export async function getAdminIntegrity(): Promise<AdminIntegritySnapshot | null> {
  return apiFetch<AdminIntegritySnapshot>('/v1/admin/integrity');
}

export async function runBootstrapRefresh(): Promise<BootstrapRunResult | null> {
  return apiFetch<BootstrapRunResult>('/v1/admin/bootstrap/run', { method: 'POST' });
}

export async function getAdminIngestionRuns(): Promise<IngestionRun[]> {
  return (await apiFetch<IngestionRun[]>('/v1/admin/ingestion-runs')) ?? [];
}

export async function getAdminNotificationHistory(): Promise<NotificationHistoryItem[]> {
  return (await apiFetch<NotificationHistoryItem[]>('/v1/admin/notifications/history')) ?? [];
}

export async function getAdminReviewItems(): Promise<ReviewItem[]> {
  return (await apiFetch<ReviewItem[]>('/v1/admin/review-items')) ?? [];
}

export async function getAdminRules(): Promise<RuleListItem[]> {
  return (await apiFetch<RuleListItem[]>('/v1/admin/rules')) ?? [];
}

export async function getAdminOpportunityDiff(id: string): Promise<Record<string, unknown> | null> {
  return apiFetch<Record<string, unknown>>(`/v1/admin/opportunities/${id}/diff`);
}

export async function runRuleTest(ruleId: string): Promise<RuleTestResult | null> {
  return apiFetch<RuleTestResult>(`/v1/admin/rules/${ruleId}/test`, { method: 'POST' });
}
