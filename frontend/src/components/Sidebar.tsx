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

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  recruiter: "Recruiter",
  candidate: "Candidate",
  viewer: "Viewer",
};

/**
 * Authenticated app shell: a persistent sidebar on desktop, a top
 * bar + slide-down drawer on narrow viewports. Only used once a user
 * is signed in - see Layout() in App.tsx, which renders the plain
 * NavBar top bar for logged-out/marketing pages instead.
 */
export default function Sidebar() {
  const navigate = useNavigate();
  const role = getStoredRole();
  const NAV_ITEMS =
    role === "candidate"
      ? CANDIDATE_NAV_ITEMS
      : RECRUITER_NAV_ITEMS;

  const [drawerOpen, setDrawerOpen] = useState(false);

  function handleLogout() {
    localStorage.removeItem("access_token");
    setDrawerOpen(false);
    navigate("/login");
  }

  function navLinkClassName({
    isActive,
  }: {
    isActive: boolean;
  }) {
    return `app-shell__nav-link${
      isActive ? " is-active" : ""
    }`;
  }

  const roleLabel = role ? ROLE_LABELS[role] ?? role : null;

  const navLinks = (
    <>
      {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={navLinkClassName}
          onClick={() => setDrawerOpen(false)}
        >
          <Icon width={17} height={17} />
          {label}
        </NavLink>
      ))}
    </>
  );

  return (
    <>
      <aside className="app-shell__sidebar">
        <Link to="/" className="app-shell__brand">
          <span className="app-topbar__brand-mark">
            <IconSparkles width={18} height={18} />
          </span>
          TalentSignal
        </Link>

        <nav className="app-shell__nav">{navLinks}</nav>

        <div className="app-shell__sidebar-footer">
          {roleLabel && (
            <div className="app-shell__profile">
              <span className="avatar" aria-hidden="true">
                {roleLabel.charAt(0)}
              </span>
              <span className="app-shell__profile-role">
                {roleLabel}
              </span>
            </div>
          )}
          <button
            type="button"
            className="btn btn-ghost btn-block"
            onClick={handleLogout}
          >
            <IconLogOut width={16} height={16} />
            Logout
          </button>
        </div>
      </aside>

      <div className="app-shell__mobile-topbar">
        <Link to="/" className="app-topbar__brand">
          <span className="app-topbar__brand-mark">
            <IconSparkles width={18} height={18} />
          </span>
          TalentSignal
        </Link>

        <button
          type="button"
          className="btn btn-ghost"
          aria-label={
            drawerOpen ? "Close menu" : "Open menu"
          }
          aria-expanded={drawerOpen}
          onClick={() => setDrawerOpen((open) => !open)}
        >
          {drawerOpen ? (
            <IconX width={18} height={18} />
          ) : (
            <IconMenu width={18} height={18} />
          )}
        </button>
      </div>

      {drawerOpen && (
        <div className="app-shell__drawer">
          <nav className="app-shell__nav">{navLinks}</nav>
          <div className="app-shell__sidebar-footer">
            <button
              type="button"
              className="btn btn-ghost btn-block"
              onClick={handleLogout}
            >
              <IconLogOut width={16} height={16} />
              Logout
            </button>
          </div>
        </div>
      )}
    </>
  );
}
