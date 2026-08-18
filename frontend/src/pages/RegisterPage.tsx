import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerUser } from "../api";
import { getApiErrorMessage } from "../api/client";
import {
  IconBarChart,
  IconBriefcase,
  IconCheck,
  IconEye,
  IconEyeOff,
  IconLock,
  IconMail,
  IconSparkles,
  IconUser,
  IconWand,
} from "../components/icons";

const MIN_PASSWORD_LENGTH = 8;

type RegistrationRole = "recruiter" | "candidate";

export default function RegisterPage() {
  const navigate = useNavigate();

  const [role, setRole] = useState<RegistrationRole>(
    "recruiter",
  );

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false);

  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<
    string | null
  >(null);

  const [emailError, setEmailError] = useState<
    string | null
  >(null);
  const [passwordError, setPasswordError] = useState<
    string | null
  >(null);
  const [confirmError, setConfirmError] = useState<
    string | null
  >(null);

  function validate(): boolean {
    let valid = true;

    setEmailError(null);
    setPasswordError(null);
    setConfirmError(null);

    if (!email.trim()) {
      setEmailError("Email is required.");
      valid = false;
    } else if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      setEmailError(
        "Enter a valid email address.",
      );
      valid = false;
    }

    if (!password) {
      setPasswordError("Password is required.");
      valid = false;
    } else if (password.length < MIN_PASSWORD_LENGTH) {
      setPasswordError(
        `Password must contain at least ${MIN_PASSWORD_LENGTH} characters.`,
      );
      valid = false;
    }

    if (!confirmPassword) {
      setConfirmError(
        "Please confirm your password.",
      );
      valid = false;
    } else if (confirmPassword !== password) {
      setConfirmError("Passwords do not match.");
      valid = false;
    }

    return valid;
  }

  async function handleRegister(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setFormError(null);

    if (!validate()) {
      return;
    }

    setLoading(true);

    try {
      await registerUser({
        email: email.trim(),
        password,
        role,
      });

      navigate("/login", {
        state: { registered: true },
      });
    } catch (err) {
      console.error("Registration failed:", err);

      setFormError(
        getApiErrorMessage(
          err,
          "Registration failed. Please try again.",
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
          <h2>
            Start screening candidates with AI
            recruitment intelligence.
          </h2>
          <p>
            Create your account to screen and rank
            candidates with AI-powered matching, backed
            by transparent evidence for every decision.
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

            <h1>Create your account</h1>
            <p className="auth-card__subtitle">
              Start screening and matching candidates
              with AI-powered recruitment intelligence.
            </p>

            <form onSubmit={handleRegister} noValidate>
              <div className="field">
                <span
                  className="field-hint"
                  style={{
                    fontSize: "0.78rem",
                    fontWeight: 650,
                    color: "var(--color-text-muted)",
                  }}
                >
                  I am registering as a
                </span>
                <div
                  role="radiogroup"
                  aria-label="I am registering as a"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "0.5rem",
                  }}
                >
                  <button
                    id="register-role-recruiter"
                    type="button"
                    role="radio"
                    aria-checked={role === "recruiter"}
                    className={`btn ${
                      role === "recruiter"
                        ? "btn-primary"
                        : "btn-secondary"
                    }`}
                    onClick={() => setRole("recruiter")}
                  >
                    <IconBriefcase width={16} height={16} />
                    Recruiter
                  </button>
                  <button
                    id="register-role-candidate"
                    type="button"
                    role="radio"
                    aria-checked={role === "candidate"}
                    className={`btn ${
                      role === "candidate"
                        ? "btn-primary"
                        : "btn-secondary"
                    }`}
                    onClick={() => setRole("candidate")}
                  >
                    <IconUser width={16} height={16} />
                    Candidate
                  </button>
                </div>
              </div>

              <div className="field">
                <label htmlFor="register-email">
                  Email
                </label>
                <div className="field-with-icon">
                  <IconMail width={16} height={16} />
                  <input
                    id="register-email"
                    type="email"
                    value={email}
                    onChange={(event) => {
                      setEmail(event.target.value);
                      setEmailError(null);
                    }}
                    autoComplete="email"
                  />
                </div>
                {emailError && (
                  <p
                    role="alert"
                    className="validation-message"
                  >
                    {emailError}
                  </p>
                )}
              </div>

              <div className="field">
                <label htmlFor="register-password">
                  Password
                </label>
                <div className="field-with-icon">
                  <IconLock width={16} height={16} />
                  <input
                    id="register-password"
                    type={
                      showPassword ? "text" : "password"
                    }
                    value={password}
                    onChange={(event) => {
                      setPassword(event.target.value);
                      setPasswordError(null);
                    }}
                    autoComplete="new-password"
                    style={{ paddingRight: "2.3rem" }}
                  />
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() =>
                      setShowPassword((value) => !value)
                    }
                    aria-label={
                      showPassword
                        ? "Hide password"
                        : "Show password"
                    }
                    style={{
                      position: "absolute",
                      right: "0.2rem",
                      top: "50%",
                      transform: "translateY(-50%)",
                      padding: "0.35rem",
                    }}
                  >
                    {showPassword ? (
                      <IconEyeOff
                        width={16}
                        height={16}
                      />
                    ) : (
                      <IconEye width={16} height={16} />
                    )}
                  </button>
                </div>
                <p className="field-hint">
                  Must be at least {MIN_PASSWORD_LENGTH}{" "}
                  characters.
                </p>
                {passwordError && (
                  <p
                    role="alert"
                    className="validation-message"
                  >
                    {passwordError}
                  </p>
                )}
              </div>

              <div className="field">
                <label htmlFor="register-confirm-password">
                  Confirm Password
                </label>
                <div className="field-with-icon">
                  <IconLock width={16} height={16} />
                  <input
                    id="register-confirm-password"
                    type={
                      showConfirmPassword
                        ? "text"
                        : "password"
                    }
                    value={confirmPassword}
                    onChange={(event) => {
                      setConfirmPassword(
                        event.target.value,
                      );
                      setConfirmError(null);
                    }}
                    autoComplete="new-password"
                    style={{ paddingRight: "2.3rem" }}
                  />
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() =>
                      setShowConfirmPassword(
                        (value) => !value,
                      )
                    }
                    aria-label={
                      showConfirmPassword
                        ? "Hide password"
                        : "Show password"
                    }
                    style={{
                      position: "absolute",
                      right: "0.2rem",
                      top: "50%",
                      transform: "translateY(-50%)",
                      padding: "0.35rem",
                    }}
                  >
                    {showConfirmPassword ? (
                      <IconEyeOff
                        width={16}
                        height={16}
                      />
                    ) : (
                      <IconEye width={16} height={16} />
                    )}
                  </button>
                </div>
                {confirmError && (
                  <p
                    role="alert"
                    className="validation-message"
                  >
                    {confirmError}
                  </p>
                )}
              </div>

              {formError && (
                <p role="alert" className="validation-message">
                  {formError}
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
                {loading
                  ? "Creating account..."
                  : "Create Account"}
              </button>
            </form>

            <p
              className="text-sm muted"
              style={{
                textAlign: "center",
                marginTop: "1.25rem",
                marginBottom: 0,
              }}
            >
              Already have an account?{" "}
              <Link to="/login">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
