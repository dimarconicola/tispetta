import { NextRequest, NextResponse } from 'next/server';

import {
  SESSION_COOKIE_DOMAIN,
  SESSION_COOKIE_NAME,
  SESSION_COOKIE_SAME_SITE,
  SESSION_COOKIE_SECURE,
} from '@/lib/env';

export async function POST(request: NextRequest) {
  const response = NextResponse.redirect(new URL('/auth/sign-in', request.url));
  response.headers.set('Cache-Control', 'no-store');
  response.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: '',
    httpOnly: true,
    sameSite: SESSION_COOKIE_SAME_SITE,
    secure: SESSION_COOKIE_SECURE,
    path: '/',
    maxAge: 0,
    ...(SESSION_COOKIE_DOMAIN ? { domain: SESSION_COOKIE_DOMAIN } : {}),
  });
  return response;
}
