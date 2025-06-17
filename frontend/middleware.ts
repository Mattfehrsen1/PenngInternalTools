import { NextResponse } from 'next/server';

export function middleware() {
  return NextResponse.next();
}

// Simplified config - avoid complex path matching
export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
