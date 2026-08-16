import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Navigate, Outlet } from "react-router-dom";

export type UserRole = "candidate" | "recruiter";

export interface AuthUser {
  email: string;
  role: UserRole;
}

interface AuthContextValue {
  user: AuthUser | null;
  login: (email: string, role: UserRole) => void;
  logout: () => void;
}

const AUTH_STORAGE_KEY = "resume-analyzer-auth-user";

const AuthContext = createContext<AuthContextValue | null>(null);

function getInitialUser(): AuthUser | null {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as AuthUser;
    if (
      parsed.email &&
      (parsed.role === "candidate" || parsed.role === "recruiter")
    ) {
      return parsed;
    }
  } catch {
    return null;
  }

  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(getInitialUser);

  const value = useMemo<AuthContextValue>(() => {
    return {
      user,
      login: (email, role) => {
        const normalizedEmail = email.trim().toLowerCase();
        const nextUser: AuthUser = {
          email: normalizedEmail,
          role,
        };

        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextUser));
        setUser(nextUser);
      },
      logout: () => {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        setUser(null);
      },
    };
  }, [user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}

export function RequireAuth() {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

export function RequireRole({ role }: { role: UserRole }) {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== role) {
    return (
      <Navigate
        to={user.role === "candidate" ? "/candidate" : "/recruiter/dashboard"}
        replace
      />
    );
  }

  return <Outlet />;
}
