import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { getStoredRole } from "../api/authRole";
import {
  IconBarChart,
  IconBriefcase,
  IconFileText,
  IconHistory,
  IconLogOut,
  IconMenu,
  IconSparkles,
  IconWand,
  IconX,
} from "./icons";

const RECRUITER_NAV_ITEMS = [
  {
    to: "/recruiter/dashboard",
    label: "Dashboard",
    icon: IconBarChart,
  },
  {
    to: "/recruiter/jobs",
    label: "Jobs",
    icon: IconBriefcase,
  },
  { to: "/resumes", label: "Resumes", icon: IconFileText },
  { to: "/screening", label: "Screening", icon: IconWand },
  { to: "/ranking", label: "Ranking", icon: IconBarChart },
  {
    to: "/screening-history",
    label: "History",
    icon: IconHistory,
  },
];

const CANDIDATE_NAV_ITEMS = [
  {
    to: "/candidate/dashboard",
    label: "Dashboard",
    icon: IconBarChart,
  },
  {
    to: "/candidate/jobs",
    label: "Jobs",
    icon: IconBriefcase,
  },
  {
    to: "/candidate/applications",
    label: "My Applications",
    icon: IconFileText,
  },
];

export default function NavBar() {
  const navigate = useNavigate();
  const isAuthenticated = Boolean(
    localStorage.getItem("access_token"),
  );

  const role = getStoredRole();
  const NAV_ITEMS =
    role === "candidate"
      ? CANDIDATE_NAV_ITEMS
      : RECRUITER_NAV_ITEMS;

  const [menuOpen, setMenuOpen] = useState(false);

  function handleLogout() {
    localStorage.removeItem("access_token");
    setMenuOpen(false);
    navigate("/login");
  }

  function navLinkClassName({
    isActive,
  }: {
    isActive: boolean;
  }) {
    return `app-topbar__link${isActive ? " is-active" : ""}`;
  }

  return (
    <div className="app-topbar">
      <div className="app-topbar__inner">
        <Link to="/" className="app-topbar__brand">
          <span className="app-topbar__brand-mark">
            <IconSparkles width={18} height={18} />
          </span>
          TalentSignal
        </Link>

        {isAuthenticated && (
          <>
            <nav className="app-topbar__links">
              {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={navLinkClassName}
                >
                  <Icon width={16} height={16} />
                  {label}
                </NavLink>
              ))}
            </nav>

            <div className="app-topbar__actions">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={handleLogout}
              >
                <IconLogOut width={16} height={16} />
                Logout
              </button>

              <button
                type="button"
                className="app-topbar__menu-btn btn btn-ghost"
                aria-label={
                  menuOpen ? "Close menu" : "Open menu"
                }
                aria-expanded={menuOpen}
                onClick={() => setMenuOpen((open) => !open)}
              >
                {menuOpen ? (
                  <IconX width={18} height={18} />
                ) : (
                  <IconMenu width={18} height={18} />
                )}
              </button>
            </div>
          </>
        )}

        {!isAuthenticated && (
          <div className="app-topbar__actions">
            <Link to="/register" className="btn btn-ghost">
              Register
            </Link>
            <Link to="/login" className="btn btn-primary">
              Login
            </Link>
          </div>
        )}
      </div>

      {isAuthenticated && (
        <div
          className={`app-topbar__mobile-panel${
            menuOpen ? " is-open" : ""
          }`}
        >
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={navLinkClassName}
              onClick={() => setMenuOpen(false)}
            >
              <Icon width={16} height={16} />
              {label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
}
