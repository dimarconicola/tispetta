import { NextRequest, NextResponse } from 'next/server';

import { APP_HOST, APP_URL, APEX_HOST, WWW_HOST } from '@/lib/hosts';

const apexPassThroughPaths = [
  '/',
  '/_next',
  '/icon.svg',
  '/manifest.webmanifest',
  '/opengraph-image',
  '/twitter-image',
  '/robots.txt',
  '/sitemap.xml',
];

export function middleware(request: NextRequest) {
  const requestHost = request.headers.get('host')?.split(':')[0];
  const pathname = request.nextUrl.pathname;

  if (requestHost === WWW_HOST) {
    const redirectUrl = new URL(request.url);
    redirectUrl.protocol = APP_URL.protocol;
    redirectUrl.host = APEX_HOST;
    return NextResponse.redirect(redirectUrl, 308);
  }

  if (requestHost === APEX_HOST) {
    const isPassThroughPath = apexPassThroughPaths.some((prefix) =>
      prefix === '/' ? pathname === '/' : pathname === prefix || pathname.startsWith(`${prefix}/`),
    );

    if (isPassThroughPath) {
      return NextResponse.next();
    }

    const redirectUrl = new URL(request.url);
    redirectUrl.protocol = APP_URL.protocol;
    redirectUrl.host = APP_HOST;
    return NextResponse.redirect(redirectUrl, 308);
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/:path*',
};
