const fallbackAppUrl = process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 'http://localhost:3000';

export const PUBLIC_APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? fallbackAppUrl;
export const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
export const INTERNAL_API_URL = process.env.INTERNAL_API_URL ?? PUBLIC_API_URL;
export const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION ?? process.env.VERCEL_GIT_COMMIT_SHA ?? 'dev';
export const APP_VERSION_LABEL = process.env.NEXT_PUBLIC_APP_VERSION_LABEL ?? (APP_VERSION === 'dev' ? 'dev' : APP_VERSION.slice(0, 7));
export const BUILD_UPDATED_AT = process.env.NEXT_PUBLIC_BUILD_UPDATED_AT || undefined;
export const BUILD_DEPLOYMENT_ID =
  process.env.NEXT_PUBLIC_BUILD_DEPLOYMENT_ID || process.env.VERCEL_DEPLOYMENT_ID || undefined;
export const GOOGLE_SITE_VERIFICATION_APP =
  (process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION_APP ?? process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION) ||
  undefined;
export const GOOGLE_SITE_VERIFICATION_APEX =
  process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION_APEX ?? GOOGLE_SITE_VERIFICATION_APP;
export const GA_MEASUREMENT_ID_APP =
  (process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID_APP ?? process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID) || undefined;
export const GA_MEASUREMENT_ID_APEX = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID_APEX ?? GA_MEASUREMENT_ID_APP;
export const SESSION_COOKIE_NAME = process.env.SESSION_COOKIE_NAME ?? 'boe_session';
export const SESSION_COOKIE_DOMAIN = process.env.SESSION_COOKIE_DOMAIN || undefined;
export const SESSION_COOKIE_SECURE =
  process.env.SESSION_COOKIE_SECURE === undefined
    ? process.env.NODE_ENV === 'production'
    : process.env.SESSION_COOKIE_SECURE === 'true';
export const SESSION_MAX_AGE_SECONDS = Number(process.env.SESSION_MAX_AGE_SECONDS ?? 60 * 60 * 24 * 14);

const sameSite = (process.env.SESSION_COOKIE_SAME_SITE ?? 'lax').toLowerCase();

export const SESSION_COOKIE_SAME_SITE: 'lax' | 'strict' | 'none' =
  sameSite === 'none' || sameSite === 'strict' ? sameSite : 'lax';
