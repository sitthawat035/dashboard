// hooks/useAuth.ts — Authentication state and login/logout logic
// isLoggedIn now lives in Zustand store, other state remains in hook (UI-only)
import { useState, useEffect, useCallback } from 'react';
import { authApi, setAuthExpiredHandler } from '../utils/api';
import { useAppStore } from '../stores/useAppStore';

export function useAuth() {
  // Read isLoggedIn from Zustand store (single source of truth)
  const isLoggedIn = useAppStore(s => s.isLoggedIn);
  const setIsLoggedIn = useAppStore(s => s.setIsLoggedIn);

  // UI-only state (not shared with other components)
  const [isLoading, setIsLoading] = useState(true);
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState(false);

  const handleLogout = useCallback(() => {
    setIsLoggedIn(false);
  }, [setIsLoggedIn]);

  // Called by any hook/component that receives a 401 on an authenticated request
  const handleAuthExpired = useCallback(() => {
    setIsLoggedIn(false);
  }, [setIsLoggedIn]);

  // Register global 401 handler for apiClient
  useEffect(() => {
    setAuthExpiredHandler(handleAuthExpired);
  }, [handleAuthExpired]);

  // Check session on mount using an AUTHENTICATED endpoint.
  useEffect(() => {
    authApi.ping().then(({ ok }) => {
      setIsLoggedIn(ok);
    }).finally(() => setIsLoading(false));
  }, [setIsLoggedIn]);

  const handleLogin = useCallback(async () => {
    try {
      const { ok } = await authApi.login(password);
      if (ok) {
        setIsLoggedIn(true);
        setLoginError(false);
      } else {
        setLoginError(true);
      }
    } catch {
      setLoginError(true);
    }
  }, [password, setIsLoggedIn]);

  return {
    isLoggedIn,
    isLoading,
    password,
    setPassword,
    loginError,
    handleLogin,
    handleLogout,
    handleAuthExpired,
  };
}
