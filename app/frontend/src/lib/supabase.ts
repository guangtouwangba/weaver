/**
 * Supabase client configuration for frontend authentication
 */

import { createBrowserClient } from '@supabase/ssr';
import type { SupabaseClient, Session, User } from '@supabase/supabase-js';

// Environment variables for Supabase
// These should be set in .env.local or via Zeabur environment
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// Validate configuration
const isConfigured = supabaseUrl && supabaseAnonKey;

// Lazy-initialized Supabase client singleton
let supabase: SupabaseClient | null = null;

/**
 * Get the Supabase client instance (lazy initialization)
 * Returns null if not configured (for anonymous-only mode)
 */
export function getSupabase(): SupabaseClient | null {
    if (!isConfigured) return null;
    
    // Only create client in browser environment
    if (typeof window === 'undefined') return null;
    
    // Create singleton instance
    if (!supabase) {
        supabase = createBrowserClient(supabaseUrl, supabaseAnonKey);
    }
    
    return supabase;
}

/**
 * Check if Supabase Auth is configured
 */
export function isAuthConfigured(): boolean {
    return Boolean(isConfigured);
}

/**
 * Get current session
 */
export async function getSession(): Promise<Session | null> {
    const client = getSupabase();
    if (!client) return null;

    const { data, error } = await client.auth.getSession();
    if (error) {
        console.error('[Supabase] Error getting session:', error);
        return null;
    }
    return data.session;
}

/**
 * Get current user
 */
export async function getUser(): Promise<User | null> {
    const client = getSupabase();
    if (!client) return null;

    const { data, error } = await client.auth.getUser();
    if (error) {
        console.error('[Supabase] Error getting user:', error);
        return null;
    }
    return data.user;
}

/**
 * Get access token for API requests
 */
export async function getAccessToken(): Promise<string | null> {
    const session = await getSession();
    return session?.access_token || null;
}

/**
 * Sign out current user
 */
export async function signOut(): Promise<void> {
    const client = getSupabase();
    if (!client) return;

    const { error } = await client.auth.signOut();
    if (error) {
        console.error('[Supabase] Error signing out:', error);
    }
}

// Re-export types
export type { Session, User };
