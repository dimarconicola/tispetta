import { cookies } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';

import { INTERNAL_API_URL, SESSION_COOKIE_NAME } from '@/lib/env';

const FORWARDED_HEADERS = ['content-type', 'accept'];

async function handle(request: NextRequest, method: string, params: { path: string[] }) {
  const path = params.path.join('/');
  const query = request.nextUrl.search;
  const url = `${INTERNAL_API_URL}/${path}${query}`;
  const cookieStore = await cookies();
  const session = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const bodyText = method === 'GET' || method === 'HEAD' ? undefined : await request.text();

  const upstream = await fetch(url, {
    method,
    headers: {
      ...Object.fromEntries(
        FORWARDED_HEADERS.map((header) => {
          const value = request.headers.get(header);
          return [header, value ?? ''];
        }).filter(([, value]) => value),
      ),
      ...(session ? { 'X-Session-Token': session } : {}),
    },
    body: bodyText && bodyText.length > 0 ? bodyText : undefined,
    cache: 'no-store',
  });

  const responseBody = await upstream.text();
  return new NextResponse(responseBody, {
    status: upstream.status,
    headers: {
      'Content-Type': upstream.headers.get('content-type') ?? 'application/json',
    },
  });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handle(request, 'GET', await context.params);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handle(request, 'POST', await context.params);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handle(request, 'PUT', await context.params);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handle(request, 'PATCH', await context.params);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handle(request, 'DELETE', await context.params);
}
