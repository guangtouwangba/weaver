'use client';

import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalBody,
    Button,
    VStack,
    Text,
    Center,
    Icon,
} from '@chakra-ui/react';
import { useRouter } from 'next/navigation';
import { FiUser, FiLock } from 'react-icons/fi';

interface AnonymousLimitPromptProps {
    isOpen: boolean;
    onClose: () => void;
    limitType: 'projects' | 'files';
}

export const AnonymousLimitPrompt = ({ isOpen, onClose, limitType }: AnonymousLimitPromptProps) => {
    const router = useRouter();

    const handleSignIn = () => {
        router.push('/login');
    };

    const title = limitType === 'projects' ? 'Project Limit Reached' : 'File Limit Reached';
    const description = limitType === 'projects'
        ? 'You have reached the limit of 3 projects for guest users. Sign in to create unlimited projects and save your work securely.'
        : 'You have reached the limit of 2 files per project for guest users. Sign in to upload more files and access advanced features.';

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="md" isCentered>
            <ModalOverlay />
            <ModalContent>
                <ModalBody p={6}>
                    <VStack spacing={6} textAlign="center">
                        <Center w={16} h={16} bg="orange.100" rounded="full" color="orange.500">
                            <Icon as={FiLock} boxSize={8} />
                        </Center>

                        <VStack spacing={2}>
                            <Text fontSize="xl" fontWeight="bold">
                                {title}
                            </Text>
                            <Text color="gray.500">
                                {description}
                            </Text>
                        </VStack>

                        <VStack spacing={3} w="full">
                            <Button
                                colorScheme="brand"
                                w="full"
                                size="lg"
                                leftIcon={<FiUser />}
                                onClick={handleSignIn}
                            >
                                Sign In / Create Account
                            </Button>
                            <Button variant="ghost" w="full" onClick={onClose}>
                                Maybe Later
                            </Button>
                        </VStack>
                    </VStack>
                </ModalBody>
            </ModalContent>
        </Modal>
    );
};
