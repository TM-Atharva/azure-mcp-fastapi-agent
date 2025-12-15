import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { PublicClientApplication, AccountInfo, AuthenticationResult } from '@azure/msal-browser';
import { msalConfig, loginRequest } from '../config/azureConfig';
import { apiClient } from '../services/api';
import type { User } from '../types';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  account: AccountInfo | null;
  accessToken: string | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const msalInstance = new PublicClientApplication(msalConfig);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [account, setAccount] = useState<AccountInfo | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      await msalInstance.initialize();

      const accounts = msalInstance.getAllAccounts();
      if (accounts.length > 0) {
        const selectedAccount = accounts[0];
        setAccount(selectedAccount);

        try {
          const token = await acquireTokenSilent(selectedAccount);
          if (token) {
            setAccessToken(token);
            apiClient.setAuthToken(token);

            const userData = await apiClient.getCurrentUser();
            setUser(userData);
            setIsAuthenticated(true);
          }
        } catch (err) {
          console.error('Silent token acquisition failed:', err);
        }
      }
    } catch (err) {
      console.error('Auth initialization failed:', err);
      setError('Failed to initialize authentication');
    } finally {
      setIsLoading(false);
    }
  };

  const acquireTokenSilent = async (account: AccountInfo): Promise<string | null> => {
    try {
      const response = await msalInstance.acquireTokenSilent({
        ...loginRequest,
        account,
      });
      return response.accessToken;
    } catch (err) {
      console.error('Silent token acquisition failed:', err);
      return null;
    }
  };

  const login = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const loginResponse: AuthenticationResult = await msalInstance.loginPopup(loginRequest);

      if (loginResponse.account) {
        setAccount(loginResponse.account);
        setAccessToken(loginResponse.accessToken);
        apiClient.setAuthToken(loginResponse.accessToken);

        const userData = await apiClient.getCurrentUser();
        setUser(userData);
        setIsAuthenticated(true);
      }
    } catch (err: any) {
      console.error('Login failed:', err);
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);

      if (account) {
        await msalInstance.logoutPopup({ account });
      }

      setIsAuthenticated(false);
      setUser(null);
      setAccount(null);
      setAccessToken(null);
      apiClient.clearAuthToken();
    } catch (err: any) {
      console.error('Logout failed:', err);
      setError(err.message || 'Logout failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        account,
        accessToken,
        login,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
