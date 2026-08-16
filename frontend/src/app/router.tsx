import { Navigate, createBrowserRouter } from "react-router-dom";

import AppLayout from "../components/layout/AppLayout";
import LoginPage from "../features/auth/LoginPage";
import ApplyJobs from "../features/candidate/ApplyJobs";
import UploadResume from "../features/candidate/UploadResume";
import JobDetailsPage from "../features/candidate/JobDetailsPage";
import Analytics from "../features/analytics/Analytics";
import Candidates from "../features/candidates/Candidates";
import Dashboard from "../features/dashboard/Dashboard";
import Jobs from "../features/jobs/Jobs";
import Resumes from "../features/resumes/Resumes";
import CreateJob from "../features/recruiter/CreateJob";
import ManageApplications from "../features/recruiter/ManageApplications";
import Screening from "../features/screening/Screening";
import { RequireAuth, RequireRole, useAuth } from "./auth";

function HomeRedirect() {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Navigate
      to={user.role === "candidate" ? "/candidate" : "/recruiter/dashboard"}
      replace
    />
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <HomeRedirect />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <RequireRole role="candidate" />,
        children: [
          {
            path: "candidate",
            element: <AppLayout />,
            children: [
              {
                index: true,
                element: <Navigate to="apply" replace />,
              },
              {
                path: "apply",
                element: <ApplyJobs />,
              },
              {
                path: "upload-resume",
                element: <UploadResume />,
              },
            ],
          },
        ],
      },
      {
        element: <RequireRole role="recruiter" />,
        children: [
          {
            path: "recruiter",
            element: <AppLayout />,
            children: [
              {
                index: true,
                element: <Navigate to="dashboard" replace />,
              },
              {
                path: "dashboard",
                element: <Dashboard />,
              },
              {
                path: "resumes",
                element: <Resumes />,
              },
              {
                path: "jobs",
                element: <Jobs />,
              },
              {
                path: "screening",
                element: <Screening />,
              },
              {
                path: "candidates",
                element: <Candidates />,
              },
              {
                path: "analytics",
                element: <Analytics />,
              },
              {
                path: "jobs/create",
                element: <CreateJob />,
              },
              {
                path: "applications",
                element: <ManageApplications />,
              },
            ],
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
