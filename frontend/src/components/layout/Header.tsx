import { LogOut, UserCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../app/auth";

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const heading =
    user?.role === "candidate" ? "Candidate Workspace" : "Recruiter Workspace";

  return (
    <header className="header">
      <div>
        <h2>{heading}</h2>
      </div>

      <div className="header-actions">
        <button className="profile-button">
          <UserCircle size={24} />

          <span>{user?.email}</span>
        </button>

        <button
          className="icon-button"
          onClick={() => {
            logout();
            navigate("/login", { replace: true });
          }}
        >
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
}
