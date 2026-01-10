'use client';

/**
 * AuthContext - Authentication state management for the application
 * 
 * Supports:
 * - Supabase authenticated users
 * - Anonymous trial users (with resource limits)
 * - Dev bypass mode (when Supabase not configured)
 */

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { Session, User, getSupabase, isAuthConfigured, getSession, signOut as supabaseSignOut } from '@/lib/supabase';
import { setAuthTokenGetter } from '@/lib/api';

// Anonymous session storage key
const ANON_SESSION_KEY = 'weaver_anon_session';
const ANON_PROJECT_COUNT_KEY = 'weaver_anon_project_count';
const ANON_FILE_COUNT_KEY = 'weaver_anon_file_count';

// Anonymous limits
const MAX_ANON_PROJECTS = 3;
const MAX_ANON_FILES = 2;

interface AuthContextType {
    // Auth state
    user: User | null;
    session: Session | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    isAnonymous: boolean;

    // Anonymous session info
    anonSessionId: string | null;
    anonProjectCount: number;
    anonFileCount: number;

    // Limit checks
    canCreateProject: boolean;
    canUploadFile: boolean;

    // Actions
    signOut: () => Promise<void>;
    updateAnonProjectCount: (count: number) => void;
    updateAnonFileCount: (count: number) => void;
    refreshSession: () => Promise<void>;
    enableGuestMode: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Generate a unique anonymous session ID
 */
function generateAnonSessionId(): string {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return 'anon-' + Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('').slice(0, 16);
}

/**
 * Get anonymous session ID from localStorage (don't auto-create)
 */
function getAnonSessionId(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(ANON_SESSION_KEY);
}

/**
 * Create anonymous session ID and store in localStorage
 */
function createAnonSessionId(): string {
    if (typeof window === 'undefined') return '';
    const sessionId = generateAnonSessionId();
    localStorage.setItem(ANON_SESSION_KEY, sessionId);
    return sessionId;
}

interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(null);
    const [session, setSession] = useState<Session | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [anonSessionId, setAnonSessionId] = useState<string | null>(null);
    const [anonProjectCount, setAnonProjectCount] = useState(0);
    const [anonFileCount, setAnonFileCount] = useState(0);

    // Initialize auth state
    useEffect(() => {
        async function initAuth() {
            try {
                const supabase = getSupabase();
                console.log('[Auth] Initializing auth, supabase configured:', !!supabase, 'isAuthConfigured:', isAuthConfigured());

                if (supabase && isAuthConfigured()) {
                    // Set up API token getter
                    setAuthTokenGetter(async () => {
                        const session = await getSession();
                        return session?.access_token || null;
                    });

                    // Get initial session
                    const currentSession = await getSession();
                    console.log('[Auth] Initial session:', currentSession ? `User: ${currentSession.user?.email}` : 'No session');
                    setSession(currentSession);
                    setUser(currentSession?.user || null);

                    // Subscribe to auth changes
                    const { data: { subscription } } = supabase.auth.onAuthStateChange(
                        async (event: string, newSession: Session | null) => {
                            setSession(newSession);
                            setUser(newSession?.user || null);

                            // Handle anonymous to authenticated migration
                            if (event === 'SIGNED_IN' && newSession) {
                                const anonId = localStorage.getItem(ANON_SESSION_KEY);
                                if (anonId) {
                                    try {
                                        // Import dynamically to avoid circular dependency issues during init
                                        const { projectsApi } = await import('@/lib/api');
                                        await projectsApi.migrate(anonId);
                                        console.log('[Auth] Successfully migrated anonymous data');

                                        // Clear anonymous API
                                        localStorage.removeItem(ANON_SESSION_KEY);
                                        localStorage.removeItem(ANON_PROJECT_COUNT_KEY);
                                        localStorage.removeItem(ANON_FILE_COUNT_KEY);
                                        setAnonSessionId(null);
                                        setAnonProjectCount(0);
                                        setAnonFileCount(0);
                                    } catch (err) {
                                        console.error('[Auth] Failed to migrate anonymous data:', err);
                                    }
                                }
                            }
                        }
                    );

                    // Cleanup subscription
                    return () => subscription.unsubscribe();
                } else {
                    // Supabase not configured - use anonymous mode
                    console.log('[Auth] Supabase not configured, using anonymous mode');
                }
            } catch (error) {
                console.error('[Auth] Error initializing auth:', error);
            } finally {
                // Check for existing anonymous session (don't auto-create)
                if (typeof window !== 'undefined') {
                    const anonId = getAnonSessionId();
                    if (anonId) {
                        setAnonSessionId(anonId);
                        // Load anonymous counts
                        const projectCount = parseInt(localStorage.getItem(ANON_PROJECT_COUNT_KEY) || '0', 10);
                        const fileCount = parseInt(localStorage.getItem(ANON_FILE_COUNT_KEY) || '0', 10);
                        setAnonProjectCount(projectCount);
                        setAnonFileCount(fileCount);
                    }
                }
                setIsLoading(false);
            }
        }

        initAuth();
    }, []);

    // Derived state
    const isAuthenticated = !!user;
    const isAnonymous = !isAuthenticated && !!anonSessionId;
    const canCreateProject = isAuthenticated || anonProjectCount < MAX_ANON_PROJECTS;
    const canUploadFile = isAuthenticated || anonFileCount < MAX_ANON_FILES;

    // Actions
    const handleSignOut = useCallback(async () => {
        await supabaseSignOut();
        setUser(null);
        setSession(null);
    }, []);

    const updateAnonProjectCount = useCallback((count: number) => {
        setAnonProjectCount(count);
        if (typeof window !== 'undefined') {
            localStorage.setItem(ANON_PROJECT_COUNT_KEY, count.toString());
        }
    }, []);

    const updateAnonFileCount = useCallback((count: number) => {
        setAnonFileCount(count);
        if (typeof window !== 'undefined') {
            localStorage.setItem(ANON_FILE_COUNT_KEY, count.toString());
        }
    }, []);

    const refreshSession = useCallback(async () => {
        const currentSession = await getSession();
        setSession(currentSession);
        setUser(currentSession?.user || null);
    }, []);

    const enableGuestMode = useCallback(() => {
        if (typeof window !== 'undefined') {
            const anonId = createAnonSessionId();
            setAnonSessionId(anonId);
            setAnonProjectCount(0);
            setAnonFileCount(0);
            localStorage.setItem(ANON_PROJECT_COUNT_KEY, '0');
            localStorage.setItem(ANON_FILE_COUNT_KEY, '0');
        }
    }, []);

    const value: AuthContextType = {
        user,
        session,
        isLoading,
        isAuthenticated,
        isAnonymous,
        anonSessionId,
        anonProjectCount,
        anonFileCount,
        canCreateProject,
        canUploadFile,
        signOut: handleSignOut,
        updateAnonProjectCount,
        updateAnonFileCount,
        refreshSession,
        enableGuestMode,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

/**
 * Hook to access auth context
 */
export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

/**
 * Hook to get token for API requests
 * Returns JWT for authenticated users, or anon session ID for anonymous users
 */
export function useAuthToken(): { getToken: () => Promise<string | null>; getUserId: () => string | null } {
    const { session, anonSessionId, isAuthenticated } = useAuth();

    const getToken = useCallback(async () => {
        if (isAuthenticated && session?.access_token) {
            return session.access_token;
        }
        return null;
    }, [isAuthenticated, session]);

    const getUserId = useCallback(() => {
        if (isAuthenticated && session?.user?.id) {
            return session.user.id;
        }
        return anonSessionId;
    }, [isAuthenticated, session, anonSessionId]);

    return { getToken, getUserId };
}
