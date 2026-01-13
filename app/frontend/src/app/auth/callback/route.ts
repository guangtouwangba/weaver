import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    const requestUrl = new URL(request.url);
    const { searchParams } = requestUrl;
    const code = searchParams.get('code');
    const next = searchParams.get('next') ?? '/dashboard';

    // Determine the correct origin
    // 1. Use NEXT_PUBLIC_SITE_URL if available (most reliable for production)
    // 2. Use X-Forwarded-Host header if available (for proxies/containers)
    // 3. Fallback to request.url origin (local development)
    let origin = requestUrl.origin;

    const siteUrl = process.env.NEXT_PUBLIC_SITE_URL;
    // Only use NEXT_PUBLIC_SITE_URL if we are NOT on localhost
    // This allows local development to work even if the env var is set globally
    if (siteUrl && requestUrl.hostname !== 'localhost' && requestUrl.hostname !== '127.0.0.1') {
        origin = siteUrl;
    } else {
        const forwardedHost = request.headers.get('x-forwarded-host');
        // If behind a proxy, likely using HTTPS, but respect proto header if present
        const forwardedProto = request.headers.get('x-forwarded-proto') || 'https';
        if (forwardedHost) {
            origin = `${forwardedProto}://${forwardedHost}`;
        }
    }

    if (code) {
        const cookieStore = await cookies();

        const supabase = createServerClient(
            process.env.NEXT_PUBLIC_SUPABASE_URL!,
            process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
            {
                cookies: {
                    getAll() {
                        return cookieStore.getAll();
                    },
                    setAll(cookiesToSet) {
                        try {
                            cookiesToSet.forEach(({ name, value, options }) =>
                                cookieStore.set(name, value, options)
                            );
                        } catch {
                            // The `setAll` method was called from a Server Component.
                            // This can be ignored if you have middleware refreshing
                            // user sessions.
                        }
                    },
                },
            }
        );

        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (!error) {
            return NextResponse.redirect(`${origin}${next}`);
        }
    }

    // URL to redirect to after sign in process completes
    return NextResponse.redirect(`${origin}/login?error=auth-code-error`);
}
