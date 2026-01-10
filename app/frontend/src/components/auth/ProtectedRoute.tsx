'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Center, Spinner, VStack, Text } from '@chakra-ui/react';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isAuthenticated, isAnonymous, isLoading } = useAuth();
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        if (!isLoading && !isAuthenticated && !isAnonymous) {
            // Redirect to login if neither authenticated nor anonymous
            router.replace(`/login?redirect=${encodeURIComponent(pathname)}`);
        }
    }, [isLoading, isAuthenticated, isAnonymous, router, pathname]);

    if (isLoading) {
        return (
            <Center h="100vh">
                <VStack spacing={4}>
                    <Spinner size="xl" color="brand.500" thickness="4px" />
                    <Text color="gray.500">Loading your workspace...</Text>
                </VStack>
            </Center>
        );
    }

    // Allow if authenticated OR anonymous
    if (isAuthenticated || isAnonymous) {
        return <>{children}</>;
    }

    return null;
}
