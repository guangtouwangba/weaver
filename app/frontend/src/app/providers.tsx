'use client';

/**
 * Client-side Providers
 *
 * Wraps the application with Chakra UI provider and any other
 * client-side context providers needed.
 */

import { ChakraProvider } from '@chakra-ui/react';
import theme from '@/theme/theme';

interface ProvidersProps {
    children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
    return <ChakraProvider theme={theme}>{children}</ChakraProvider>;
}
