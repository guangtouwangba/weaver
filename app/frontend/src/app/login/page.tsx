'use client';

import { Suspense, useEffect, useState } from 'react';
import { Box, Container, Heading, Text, VStack, Card, CardBody, Divider, Button } from '@chakra-ui/react';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { useRouter, useSearchParams } from 'next/navigation';
import { getSupabase, isAuthConfigured } from '@/lib/supabase';
import { useAuth } from '@/contexts/AuthContext';

function LoginContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { isAuthenticated, isAnonymous, isLoading, enableGuestMode } = useAuth();
    const [supabase] = useState(() => getSupabase());

    const redirectTo = searchParams.get('redirect') || '/dashboard';
    const isSupabaseConfigured = isAuthConfigured();

    useEffect(() => {
        // Redirect if already authenticated or in guest mode
        if (isAuthenticated || isAnonymous) {
            router.replace(redirectTo);
        }
    }, [isAuthenticated, isAnonymous, router, redirectTo]);

    // Handle OAuth implicit flow - token might be in URL hash
    useEffect(() => {
        if (supabase && typeof window !== 'undefined') {
            // Check if there's a hash with access_token (implicit flow)
            const hash = window.location.hash;
            console.log('[Login] Checking URL hash:', hash ? 'Has hash' : 'No hash');

            if (hash && hash.includes('access_token')) {
                console.log('[Login] Found access_token in hash, getting session...');
                // Supabase client will automatically detect and set the session from URL
                supabase.auth.getSession().then(({ data: { session }, error }) => {
                    console.log('[Login] Session result:', session ? `User: ${session.user?.email}` : 'No session', error ? `Error: ${error.message}` : '');
                    if (session) {
                        // Clear the hash and redirect
                        window.history.replaceState(null, '', window.location.pathname);
                        router.replace(redirectTo);
                    }
                });
            }
        }
    }, [supabase, router, redirectTo]);

    const handleGuestMode = () => {
        enableGuestMode();
        router.push(redirectTo);
    };

    if (isLoading) {
        return (
            <Container maxW="container.sm" py={20}>
                <Text textAlign="center">Loading...</Text>
            </Container>
        );
    }

    // Handle case where Supabase is not configured (local dev)
    if (!supabase || !isSupabaseConfigured) {
        return (
            <Container maxW="container.sm" py={20}>
                <Card variant="outline" borderColor="border.subtle">
                    <CardBody>
                        <VStack spacing={6} align="stretch" textAlign="center">
                            <Heading size="lg">Authentication Not Configured</Heading>
                            <Text color="fg.muted">
                                Supabase credentials are missing securely. You are seeing this because the app is running in development mode without Auth keys.
                            </Text>

                            <Box p={4} bg="bg.subtle" borderRadius="md" textAlign="left">
                                <Text fontSize="sm" fontFamily="mono">
                                    SUPABASE_URL=...<br />
                                    SUPABASE_ANON_KEY=...
                                </Text>
                            </Box>

                            <Text fontSize="sm">
                                For now, you are using an <strong>Anonymous Session</strong> which allows trying the app with limitations.
                            </Text>

                            <Button
                                colorScheme="brand"
                                onClick={handleGuestMode}
                            >
                                Continue as Guest
                            </Button>
                        </VStack>
                    </CardBody>
                </Card>
            </Container>
        );
    }

    const getRedirectUrl = () => {
        if (typeof window === 'undefined') return '';

        // Fix: If running on localhost, always redirect back to localhost
        // to avoid production redirect loops during development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return `${window.location.origin}/auth/callback`;
        }

        const siteUrl = process.env.NEXT_PUBLIC_SITE_URL;
        if (siteUrl) {
            return `${siteUrl}/auth/callback`;
        }
        // Fallback to window origin
        return `${window.location.origin}/auth/callback`;
    };

    return (
        <Container maxW="container.sm" py={20}>
            <VStack spacing={8} align="stretch">
                <Box textAlign="center">
                    <Heading size="xl" mb={2}>Welcome Back</Heading>
                    <Text color="fg.muted">Sign in to access your research projects</Text>
                </Box>

                <Card variant="outline" borderColor="border.subtle">
                    <CardBody>
                        <Auth
                            supabaseClient={supabase}
                            appearance={{
                                theme: ThemeSupa,
                                variables: {
                                    default: {
                                        colors: {
                                            brand: '#3182ce',
                                            brandAccent: '#2b6cb0',
                                        },
                                    },
                                },
                            }}
                            providers={['google', 'github']}
                            redirectTo={getRedirectUrl()}
                            onlyThirdPartyProviders={false}
                            magicLink={true}
                        />
                    </CardBody>
                </Card>

                <Box textAlign="center">
                    <Divider my={4} />
                    <Text color="fg.muted" fontSize="sm" mb={4}>
                        New to Research Agent?
                    </Text>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleGuestMode}
                    >
                        Try without account (Guest Mode)
                    </Button>
                </Box>
            </VStack>
        </Container>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={
            <Container maxW="container.sm" py={20}>
                <Text textAlign="center">Loading...</Text>
            </Container>
        }>
            <LoginContent />
        </Suspense>
    );
}
