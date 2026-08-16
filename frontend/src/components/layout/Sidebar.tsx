import {
  BarChart3,
  BriefcaseBusiness,
  LayoutDashboard,
  ClipboardList,
  Search,
  FileText,
  FileUp,
  PlusCircle,
  Users,
} from "lucide-react";

import { NavLink } from "react-router-dom";
import { useAuth } from "../../app/auth";

const candidateNavigation = [
  {
    name: "Apply Jobs",
    path: "/candidate/apply",
    icon: BriefcaseBusiness,
  },
  {
    name: "Upload Resume",
    path: "/candidate/upload-resume",
    icon: FileUp,
  },
];

const recruiterNavigation = [
  {
    name: "Dashboard",
    path: "/recruiter/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Resumes",
    path: "/recruiter/resumes",
    icon: FileText,
  },
  {
    name: "Jobs",
    path: "/recruiter/jobs",
    icon: BriefcaseBusiness,
  },
  {
    name: "Screening",
    path: "/recruiter/screening",
    icon: Search,
  },
  {
    name: "Candidates",
    path: "/recruiter/candidates",
    icon: Users,
  },
  {
    name: "Analytics",
    path: "/recruiter/analytics",
    icon: BarChart3,
  },
  {
    name: "Create Job",
    path: "/recruiter/jobs/create",
    icon: PlusCircle,
  },
  {
    name: "Manage Applications",
    path: "/recruiter/applications",
    icon: ClipboardList,
  },
];

export default function Sidebar() {
  const { user } = useAuth();
  const navigation =
    user?.role === "candidate" ? candidateNavigation : recruiterNavigation;

  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-icon">
          <FileText size={19} />
        </div>

        <div>
          <h1>ResumeAI</h1>
          <span>Resume Analyzer</span>
        </div>
      </div>

      <nav className="navigation">
        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              end
              className={({ isActive }) =>
                `nav-item ${isActive ? "active" : ""}`
              }
            >
              <Icon size={19} />

              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
