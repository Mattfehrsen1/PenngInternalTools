'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface AuthContextType {
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  token: string | null;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setTokenState] = useState<string | null>(null);
  const router = useRouter();

  const setToken = (newToken: string | null) => {
    console.log('💾 Setting token:', newToken ? 'token provided' : 'null');
    setTokenState(newToken);
    if (newToken) {
      localStorage.setItem('auth_token', newToken);
      console.log('💾 Token saved to localStorage');
    } else {
      localStorage.removeItem('auth_token');
      console.log('💾 Token removed from localStorage');
    }
  };

  useEffect(() => {
    console.log('🔐 Auth state check - token:', token ? 'exists' : 'null', 'isAuthenticated:', isAuthenticated);
    if (token) {
      setIsAuthenticated(true);
    }
  }, [token]);

  useEffect(() => {
    // Check if token exists in localStorage on component mount
    console.log('🔍 Checking for saved token...');
    const savedToken = localStorage.getItem('auth_token');
    if (savedToken) {
      console.log('✅ Found saved token, setting authentication state');
      setTokenState(savedToken);
      setIsAuthenticated(true);
    } else {
      console.log('❌ No saved token found');
    }
  }, []);

  const login = async (username: string, password: string) => {
    console.log(' AuthProvider.login called with:', { username, password: password.substring(0, 3) + '...' });
    try {
      console.log(' Calling api.login...');
      const response = await api.login(username, password);
      console.log(' API response received:', { access_token: response.access_token.substring(0, 20) + '...' });
      setToken(response.access_token);
      setIsAuthenticated(true);
      console.log('🎯 Authentication state updated, redirecting to /chat...');
      router.push('/chat');
    } catch (error) {
      console.error(' AuthProvider login error:', error);
      throw error;
    }
  };

  const logout = () => {
    api.clearToken();
    setToken(null);
    setIsAuthenticated(false);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, token }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
