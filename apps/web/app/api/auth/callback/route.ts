import { NextRequest, NextResponse } from 'next/server';

import {
  INTERNAL_API_URL,
  SESSION_COOKIE_DOMAIN,
  SESSION_COOKIE_NAME,
  SESSION_COOKIE_SAME_SITE,
  SESSION_COOKIE_SECURE,
  SESSION_MAX_AGE_SECONDS,
} from '@/lib/env';

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get('token');
  if (!token) {
    return NextResponse.redirect(new URL('/auth/sign-in?error=missing_token', request.url));
  }

  const exchangeResponse = await fetch(`${INTERNAL_API_URL}/v1/auth/exchange-magic-link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
    cache: 'no-store',
  });

  if (!exchangeResponse.ok) {
    return NextResponse.redirect(new URL('/auth/sign-in?error=magic_link_invalid', request.url));
  }

  const payload = (await exchangeResponse.json()) as { redirect_to?: string; session_token: string };
  const redirectTo = payload.redirect_to?.startsWith('/') ? payload.redirect_to : '/onboarding';
  const response = NextResponse.redirect(new URL(redirectTo, request.url));
  response.headers.set('Cache-Control', 'no-store');
  response.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: payload.session_token,
    httpOnly: true,
    sameSite: SESSION_COOKIE_SAME_SITE,
    secure: SESSION_COOKIE_SECURE,
    path: '/',
    maxAge: SESSION_MAX_AGE_SECONDS,
    ...(SESSION_COOKIE_DOMAIN ? { domain: SESSION_COOKIE_DOMAIN } : {}),
  });
  return response;
}
