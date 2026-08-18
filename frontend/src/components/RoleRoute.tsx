import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { getStoredRole, type UserRole } from "../api/authRole";

type RoleRouteProps = {
  allow: UserRole[];
  children: ReactNode;
};

/**
 * Frontend-level route guard. This improves UX (candidates never
 * see a flash of recruiter-only UI, and vice versa) but is not the
 * security boundary - every protected endpoint independently
 * enforces role/ownership server-side regardless of what this
 * component allows to render.
 */
export default function RoleRoute({
  allow,
  children,
}: RoleRouteProps) {
  const role = getStoredRole();

  if (!role) {
    return <Navigate to="/login" replace />;
  }

  if (!allow.includes(role)) {
    return (
      <Navigate
        to={role === "candidate" ? "/candidate/dashboard" : "/jobs"}
        replace
      />
    );
  }

  return <>{children}</>;
}
