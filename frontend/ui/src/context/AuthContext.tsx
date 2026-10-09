import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { authService, SESSION_KEY } from "@/services/api";
import type { AuthResponse } from "@/types";

interface AuthContextValue {
  session: AuthResponse | null;
  signIn: (email: string, password: string) => Promise<AuthResponse>;
  register: (name: string, email: string, password: string) => Promise<AuthResponse>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readSession(): AuthResponse | null {
  try {
    const value = sessionStorage.getItem(SESSION_KEY);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthResponse | null>(readSession);
  const save = (next: AuthResponse) => {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(next));
    setSession(next);
    return next;
  };
  const value = useMemo(() => ({
    session,
    signIn: async (email: string, password: string) => save(await authService.login(email, password)),
    register: async (name: string, email: string, password: string) => save(await authService.register(name, email, password)),
    signOut: () => { sessionStorage.removeItem(SESSION_KEY); setSession(null); },
  }), [session]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
