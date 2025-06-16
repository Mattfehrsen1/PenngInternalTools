import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Let client-side handle all authentication
  return NextResponse.next();
}

export const config = {
  matcher: [
    // Only apply to specific paths to avoid conflicts
    '/chat/:path*',
    '/files/:path*',
    '/prompts/:path*',
    '/voice/:path*',
  ],
};
