import { useEffect, useRef, useState } from "react";
import { googleAuth } from "../api";
import { getApiErrorMessage } from "../api/client";
import {
  GOOGLE_CLIENT_ID,
  isGoogleSignInConfigured,
  loadGoogleIdentityScript,
} from "../lib/googleIdentity";

type RegistrationRole = "recruiter" | "candidate";

type GoogleSignInButtonProps = {
  /**
   * Only meaningful for a brand-new Google account - ignored by the
   * backend for an account that has already signed in with Google
   * before. Omit on the Login page; pass the selected role on the
   * Register page.
   */
  role?: RegistrationRole;
  onSuccess: (accessToken: string) => void;
  onError: (message: string) => void;
};

/**
 * Renders the real Google Identity Services button (not a look-alike)
 * and exchanges the resulting ID token for the application's own JWT
 * via POST /api/auth/google. See src/lib/googleIdentity.ts and
 * Google's own guidance:
 * https://developers.google.com/identity/gsi/web/guides/display-button
 */
export default function GoogleSignInButton({
  role,
  onSuccess,
  onError,
}: GoogleSignInButtonProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<
    "loading" | "ready" | "unavailable" | "exchanging"
  >(isGoogleSignInConfigured() ? "loading" : "unavailable");

  useEffect(() => {
    if (!isGoogleSignInConfigured()) {
      return;
    }

    let cancelled = false;

    async function handleCredential(
      response: { credential: string },
    ) {
      setStatus("exchanging");

      try {
        const token = await googleAuth({
          credential: response.credential,
          role,
        });
        onSuccess(token.access_token);
      } catch (err) {
        onError(
          getApiErrorMessage(
            err,
            "Google sign-in failed. Please try again.",
          ),
        );
      } finally {
        if (!cancelled) {
          setStatus("ready");
        }
      }
    }

    loadGoogleIdentityScript()
      .then(() => {
        if (cancelled || !containerRef.current) {
          return;
        }

        window.google?.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleCredential,
          ux_mode: "popup",
        });

        containerRef.current.innerHTML = "";

        window.google?.accounts.id.renderButton(
          containerRef.current,
          {
            type: "standard",
            theme: "outline",
            size: "large",
            text: role ? "signup_with" : "signin_with",
            shape: "rectangular",
            width: 328,
          },
        );

        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) {
          setStatus("unavailable");
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role]);

  if (status === "unavailable") {
    return (
      <div className="google-signin google-signin--unavailable">
        Google Sign-In is not configured for this environment.
      </div>
    );
  }

  return (
    <div className="google-signin">
      <div
        ref={containerRef}
        aria-label={
          role
            ? "Sign up with Google"
            : "Continue with Google"
        }
      />
      {status === "loading" && (
        <span
          className="spinner-inline"
          aria-hidden="true"
          style={{ marginLeft: "0.5rem" }}
        />
      )}
      {status === "exchanging" && (
        <p
          role="status"
          className="muted text-sm"
          style={{ marginTop: "0.5rem" }}
        >
          <span
            className="spinner-inline"
            aria-hidden="true"
            style={{ marginRight: "0.4rem" }}
          />
          Signing in with Google...
        </p>
      )}
    </div>
  );
}
