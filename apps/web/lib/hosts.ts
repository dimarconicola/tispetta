import { PUBLIC_APP_URL } from '@/lib/env';

const appUrl = new URL(PUBLIC_APP_URL);

export const APP_URL = appUrl;
export const APP_HOST = appUrl.host;
export const APEX_HOST = APP_HOST.startsWith('app.') ? APP_HOST.slice(4) : APP_HOST;
export const WWW_HOST = `www.${APEX_HOST}`;

export function isApexLikeHost(host: string | null | undefined) {
  if (!host) {
    return false;
  }

  const normalizedHost = host.split(':')[0];
  return normalizedHost === APEX_HOST || normalizedHost === WWW_HOST;
}

export function isAppHost(host: string | null | undefined) {
  if (!host) {
    return false;
  }

  return host.split(':')[0] === APP_HOST;
}
