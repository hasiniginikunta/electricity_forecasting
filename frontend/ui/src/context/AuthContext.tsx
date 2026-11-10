import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { authService, householdService, SESSION_KEY } from "@/services/api";
import type { AuthResponse, Household } from "@/types";

interface AuthContextValue {
  session: AuthResponse | null;
  household: Household | null;
  householdId: number | null;
  signIn: (email: string, password: string) => Promise<AuthResponse>;
  register: (name: string, email: string, password: string) => Promise<AuthResponse>;
  signOut: () => void;
  refreshHousehold: () => Promise<void>;
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
  const [household, setHousehold] = useState<Household | null>(null);

  const saveSession = (next: AuthResponse) => {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(next));
    setSession(next);
    return next;
  };

  const refreshHousehold = async () => {
    const s = session ?? readSession();
    if (!s?.userId) return;
    try {
      const hh = await householdService.getByUserId(s.userId);
      setHousehold(hh);
    } catch {
      // household not created yet (new user going through onboarding)
    }
  };

  // Resolve household whenever session changes
  useEffect(() => {
    if (session?.userId) refreshHousehold();
    else setHousehold(null);
  }, [session?.userId]);

  const value = useMemo<AuthContextValue>(() => ({
    session,
    household,
    householdId: household?.id ?? null,
    signIn: async (email, password) => {
      const next = saveSession(await authService.login(email, password));
      return next;
    },
    register: async (name, email, password) => {
      const next = saveSession(await authService.register(name, email, password));
      return next;
    },
    signOut: () => {
      sessionStorage.removeItem(SESSION_KEY);
      setSession(null);
      setHousehold(null);
    },
    refreshHousehold,
  }), [session, household]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
