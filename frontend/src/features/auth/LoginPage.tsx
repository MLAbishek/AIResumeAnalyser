import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { useAuth, type UserRole } from "../../app/auth";

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("candidate");

  if (user) {
    return (
      <Navigate
        to={user.role === "candidate" ? "/candidate" : "/recruiter/dashboard"}
        replace
      />
    );
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!email.trim() || !password.trim()) {
      return;
    }

    login(email, role);
    navigate(role === "candidate" ? "/candidate" : "/recruiter/dashboard", {
      replace: true,
    });
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <p className="auth-kicker">AI Resume Analyzer</p>
        <h1>Sign in to continue</h1>
        <p className="auth-subtitle">
          Candidates can only apply to jobs and upload resumes. Recruiters can
          create jobs and manage applications.
        </p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Work Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@company.com"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter password"
              required
            />
          </label>

          <div className="role-switch" role="group" aria-label="Role selection">
            <button
              type="button"
              className={role === "candidate" ? "active" : ""}
              onClick={() => setRole("candidate")}
            >
              Candidate
            </button>
            <button
              type="button"
              className={role === "recruiter" ? "active" : ""}
              onClick={() => setRole("recruiter")}
            >
              Recruiter
            </button>
          </div>

          <button type="submit" className="auth-submit">
            Continue as {role}
          </button>
        </form>
      </div>
    </div>
  );
}
