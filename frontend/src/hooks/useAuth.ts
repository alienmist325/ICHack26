import { createContext, useState, useCallback, useEffect, useContext } from 'react';
import { api } from '../api/client';

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface AuthUser {
  id: number;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface AuthContextType {
  user: AuthUser | null;
  tokens: AuthTokens | null;
  isLoading: boolean;
  error: string | null;
  register: (email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function useSetupAuth(): AuthContextType {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load tokens from localStorage on mount
  useEffect(() => {
    const storedTokens = localStorage.getItem('auth_tokens');
    if (storedTokens) {
      try {
        const parsed = JSON.parse(storedTokens);
        setTokens(parsed);
        
        // Try to fetch user info using the access token
        // Tokens are stored in camelCase (accessToken)
        fetchCurrentUser(parsed.accessToken);
      } catch (err) {
        console.error('Failed to parse stored tokens:', err);
        localStorage.removeItem('auth_tokens');
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchCurrentUser = useCallback(async (accessToken: string) => {
    try {
      const response = await fetch('http://localhost:8000/auth/me', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        setTokens(null);
        localStorage.removeItem('auth_tokens');
      }
    } catch (err) {
      console.error('Failed to fetch user:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Registration failed');
      }

      const tokenData = await response.json();
      // Convert API response (snake_case) to camelCase for consistent internal use
      const normalizedTokens = {
        accessToken: tokenData.access_token,
        refreshToken: tokenData.refresh_token,
        tokenType: tokenData.token_type,
        expiresIn: tokenData.expires_in,
      };
      setTokens(normalizedTokens);
      localStorage.setItem('auth_tokens', JSON.stringify(normalizedTokens));

      // Fetch user info
      await fetchCurrentUser(normalizedTokens.accessToken);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Registration failed';
      setError(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchCurrentUser]);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Invalid email or password');
      }

      const tokenData = await response.json();
      // Convert API response (snake_case) to camelCase for consistent internal use
      const normalizedTokens = {
        accessToken: tokenData.access_token,
        refreshToken: tokenData.refresh_token,
        tokenType: tokenData.token_type,
        expiresIn: tokenData.expires_in,
      };
      setTokens(normalizedTokens);
      localStorage.setItem('auth_tokens', JSON.stringify(normalizedTokens));

      // Fetch user info
      await fetchCurrentUser(normalizedTokens.accessToken);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Login failed';
      setError(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchCurrentUser]);

  const logout = useCallback(() => {
    setUser(null);
    setTokens(null);
    setError(null);
    localStorage.removeItem('auth_tokens');
  }, []);

  const refreshAccessToken = useCallback(async () => {
    if (!tokens?.refreshToken) {
      logout();
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/auth/refresh', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${tokens.refreshToken}`,
        },
      });

      if (!response.ok) {
        logout();
        return;
      }

      const tokenData = await response.json();
      // Convert API response (snake_case) to camelCase for consistent internal use
      const normalizedTokens = {
        accessToken: tokenData.access_token,
        refreshToken: tokenData.refresh_token,
        tokenType: tokenData.token_type,
        expiresIn: tokenData.expires_in,
      };
      setTokens(normalizedTokens);
      localStorage.setItem('auth_tokens', JSON.stringify(normalizedTokens));
    } catch (err) {
      console.error('Token refresh failed:', err);
      logout();
    }
  }, [tokens, logout]);

  return {
    user,
    tokens,
    isLoading,
    error,
    register,
    login,
    logout,
    refreshAccessToken,
    isAuthenticated: !!user,
  };
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}


