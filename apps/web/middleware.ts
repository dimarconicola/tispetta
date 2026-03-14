import { NextRequest, NextResponse } from 'next/server';

import { PUBLIC_APP_URL } from '@/lib/env';

const appUrl = new URL(PUBLIC_APP_URL);
const appHost = appUrl.host;
const apexHost = appHost.startsWith('app.') ? appHost.slice(4) : appHost;
const redirectHosts = new Set([apexHost, `www.${apexHost}`]);

export function middleware(request: NextRequest) {
  const requestHost = request.headers.get('host')?.split(':')[0];

  if (requestHost && redirectHosts.has(requestHost) && requestHost !== appHost) {
    const redirectUrl = new URL(request.url);
    redirectUrl.protocol = appUrl.protocol;
    redirectUrl.host = appHost;
    return NextResponse.redirect(redirectUrl, 308);
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/:path*',
};
