import {
    Menu,
    MenuButton,
    MenuList,
    MenuItem,
    MenuDivider,
    Button,
    Avatar,
    Text,
    VStack,
    HStack,
    Box,
    Badge,
    Icon,
    IconButton,
    Tooltip,
} from '@chakra-ui/react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { FiChevronDown, FiLogOut, FiUser, FiSettings } from 'react-icons/fi';

interface UserMenuProps {
    minimized?: boolean;
}

export const UserMenu = ({ minimized = false }: UserMenuProps) => {
    const router = useRouter();
    const { user, signOut, isAnonymous, anonProjectCount, anonFileCount } = useAuth();

    const handleSignOut = async () => {
        await signOut();
        router.push('/login');
    };

    const handleSignIn = () => {
        router.push('/login');
    };

    if (!user && !isAnonymous) {
        if (minimized) {
            return (
                <Tooltip label="Sign In" placement="right">
                    <IconButton
                        icon={<FiUser />}
                        aria-label="Sign In"
                        onClick={handleSignIn}
                        rounded="full"
                        colorScheme="brand"
                        size="sm"
                    />
                </Tooltip>
            );
        }

        return (
            <Button
                width="full"
                colorScheme="brand"
                size="sm"
                onClick={handleSignIn}
            >
                Sign In
            </Button>
        );
    }

    return (
        <Menu placement="right-end">
            {minimized ? (
                <Tooltip label={user?.email || 'Guest User'} placement="right">
                    <MenuButton
                        as={IconButton}
                        rounded="full"
                        size="sm"
                        aria-label="User Menu"
                    >
                        <Avatar
                            size="sm"
                            name={user?.email || 'Guest'}
                            src={user?.user_metadata?.avatar_url}
                            cursor="pointer"
                        />
                    </MenuButton>
                </Tooltip>
            ) : (
                <MenuButton
                    as={Button}
                    variant="ghost"
                    width="full"
                    p={2}
                    height="auto"
                >
                    <HStack spacing={3} width="full">
                        <Avatar
                            size="sm"
                            name={user?.email || 'Guest'}
                            src={user?.user_metadata?.avatar_url}
                        />
                        <VStack align="start" spacing={0} flex={1} overflow="hidden">
                            <Text fontSize="sm" fontWeight="medium" isTruncated width="full" textAlign="left">
                                {user?.email || 'Guest User'}
                            </Text>
                            <Text fontSize="xs" color="gray.500" isTruncated width="full" textAlign="left">
                                {isAnonymous ? 'Trial Mode' : 'Pro Plan'}
                            </Text>
                        </VStack>
                        <Icon as={FiChevronDown} color="gray.400" />
                    </HStack>
                </MenuButton>
            )}
            <MenuList>
                {isAnonymous && (
                    <>
                        <Box px={3} py={2}>
                            <Text fontSize="xs" fontWeight="bold" color="gray.500" mb={1} textTransform="uppercase">
                                Trial Usage
                            </Text>
                            <HStack justify="space-between" mb={1}>
                                <Text fontSize="xs">Projects</Text>
                                <Badge colorScheme={anonProjectCount >= 3 ? 'red' : 'green'}>
                                    {anonProjectCount}/3
                                </Badge>
                            </HStack>
                            <HStack justify="space-between">
                                <Text fontSize="xs">Files</Text>
                                <Badge colorScheme={anonFileCount >= 2 ? 'red' : 'green'}>
                                    {anonFileCount}/2
                                </Badge>
                            </HStack>
                        </Box>
                        <MenuDivider />
                        <MenuItem icon={<FiUser />} onClick={handleSignIn} color="brand.500" fontWeight="medium">
                            Sign In to Save Work
                        </MenuItem>
                    </>
                )}

                {!isAnonymous && (
                    <MenuItem icon={<FiSettings />} onClick={() => router.push('/settings')}>
                        Settings
                    </MenuItem>
                )}

                <MenuDivider />
                <MenuItem icon={<FiLogOut />} onClick={handleSignOut} color="red.500">
                    Sign Out
                </MenuItem>
            </MenuList>
        </Menu>
    );
};
