/**
 * Next.js Middleware
 * Handles auth session refresh and route protection for protected routes only.
 */
import { type NextRequest } from "next/server";
import { updateSession } from "@/lib/supabase/middleware";

export async function middleware(request: NextRequest) {
  return await updateSession(request);
}

export const config = {
  matcher: [
    // Only run middleware on protected routes - not on all requests
    "/dashboard/:path*",
    "/workspace/:path*",
  ],
};
