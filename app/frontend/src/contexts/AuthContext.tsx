'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { DEFAULT_USER_ID } from '@/lib/api';

export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  // Mock initial user using the default ID
  // In a real app, this would fetch from an auth provider (Auth0, Supabase, etc.)
  const [user, setUser] = useState<User | null>({
    id: DEFAULT_USER_ID,
    name: 'You', // Default display name
    email: 'user@example.com'
  });

  const [isLoading, setIsLoading] = useState(false);

  const login = async () => {
    setIsLoading(true);
    // Simulate login delay
    await new Promise(resolve => setTimeout(resolve, 500));

    setUser({
      id: DEFAULT_USER_ID,
      name: 'You',
      email: 'user@example.com'
    });
    setIsLoading(false);
  };

  const logout = async () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
