import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { login } from "../api";
import { getApiErrorMessage } from "../api/client";
import { getStoredRole } from "../api/authRole";
import GoogleSignInButton from "../components/GoogleSignInButton";
import {
  IconBarChart,
  IconCheck,
  IconLock,
  IconMail,
  IconSparkles,
  IconWand,
} from "../components/icons";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const justRegistered = Boolean(
    (location.state as { registered?: boolean } | null)
      ?.registered,
  );

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function completeAuth(accessToken: string) {
    localStorage.setItem("access_token", accessToken);

    // Candidates land in their own portal; every other existing
    // role (recruiter/admin/viewer) keeps the original /jobs
    // destination unchanged.
    navigate(
      getStoredRole() === "candidate"
        ? "/candidate/dashboard"
        : "/jobs",
    );
  }

  async function handleLogin(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setLoading(true);
    setError(null);

    try {
      const response = await login({
        email,
        password,
      });

      completeAuth(response.access_token);
    } catch (err) {
      console.error("Login failed:", err);
      setError(
        getApiErrorMessage(
          err,
          "Invalid email or password.",
        ),
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: "none", padding: 0 }}>
      <div className="auth-shell">
        <div className="auth-shell__brand">
          <IconSparkles width={30} height={30} />
          <h2>Recruitment intelligence, built on evidence.</h2>
          <p>
            Screen and rank candidates with AI-assisted matching,
            backed by transparent, citation-level evidence for
            every decision.
          </p>

          <ul className="auth-shell__brand-list">
            <li>
              <IconWand width={16} height={16} />
              Guided AI screening workflow
            </li>
            <li>
              <IconBarChart width={16} height={16} />
              Explainable candidate ranking
            </li>
            <li>
              <IconCheck width={16} height={16} />
              Full evidence &amp; decision traceability
            </li>
          </ul>
        </div>

        <div className="auth-shell__form-side">
          <div className="auth-card">
            <span className="auth-card__mark">
              <IconSparkles width={20} height={20} />
            </span>

            <h1>Login</h1>
            <p className="auth-card__subtitle">
              Welcome back — sign in to continue screening.
            </p>

            {justRegistered && (
              <p
                role="status"
                className="badge badge-success"
                style={{ marginBottom: "1rem" }}
              >
                Account created — please sign in.
              </p>
            )}

            <form onSubmit={handleLogin}>
              <div className="field">
                <label htmlFor="email">Email</label>
                <div className="field-with-icon">
                  <IconMail width={16} height={16} />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(event) =>
                      setEmail(event.target.value)
                    }
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              <div className="field">
                <label htmlFor="password">Password</label>
                <div className="field-with-icon">
                  <IconLock width={16} height={16} />
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
                    autoComplete="current-password"
                    required
                  />
                </div>
              </div>

              {error && (
                <p role="alert" className="validation-message">
                  {error}
                </p>
              )}

              <button
                type="submit"
                className="btn btn-primary btn-block"
                disabled={loading}
              >
                {loading && (
                  <span
                    className="spinner-inline"
                    aria-hidden="true"
                  />
                )}
                {loading ? "Logging in..." : "Login"}
              </button>
            </form>

            <div className="auth-divider" role="separator">
              <span>or</span>
            </div>

            <GoogleSignInButton
              onSuccess={completeAuth}
              onError={setError}
            />

            <p
              className="text-sm muted"
              style={{
                textAlign: "center",
                marginTop: "1.25rem",
                marginBottom: 0,
              }}
            >
              Don&apos;t have an account?{" "}
              <Link to="/register">Create one</Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
