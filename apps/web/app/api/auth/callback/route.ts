import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get('token');
  if (!token) {
    return NextResponse.redirect(new URL('/auth/sign-in', request.url));
  }
  return NextResponse.redirect(`${API_URL}/v1/auth/verify-magic-link?token=${encodeURIComponent(token)}`);
}
