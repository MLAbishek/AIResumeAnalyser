export type UserRole =
  | "admin"
  | "recruiter"
  | "viewer"
  | "candidate";

/**
 * Decode the role claim already embedded in the access token
 * (see app/auth/jwt.py create_access_token) without adding a
 * JWT-decoding dependency - this is a display/navigation hint
 * only. The backend independently enforces every role check on
 * every request; nothing here is a security boundary.
 */
export function getStoredRole(): UserRole | null {
  const token = localStorage.getItem("access_token");

  if (!token) {
    return null;
  }

  try {
    const payload = token.split(".")[1];
    const decoded = atob(
      payload.replace(/-/g, "+").replace(/_/g, "/"),
    );

    const parsed: unknown = JSON.parse(decoded);

    if (
      typeof parsed === "object" &&
      parsed !== null &&
      "role" in parsed &&
      typeof (parsed as { role: unknown }).role === "string"
    ) {
      return (parsed as { role: UserRole }).role;
    }

    return null;
  } catch {
    return null;
  }
}

export function isCandidate(): boolean {
  return getStoredRole() === "candidate";
}

export function isRecruiterOrAdmin(): boolean {
  const role = getStoredRole();
  return role === "recruiter" || role === "admin";
}
