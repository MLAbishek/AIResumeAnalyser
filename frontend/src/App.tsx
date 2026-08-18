import { useEffect, useState } from "react";
import { Link, Navigate, Outlet, Route, Routes } from "react-router-dom";
import JobsPage from "./pages/JobsPage";
import ResumesPage from "./pages/ResumesPage";
import ScreeningPage from "./pages/ScreeningPage";
import RankingPage from "./pages/RankingPage";
import CandidateMatchProfilePage from "./pages/CandidateMatchProfilePage";
import ScreeningHistoryPage from "./pages/ScreeningHistoryPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import RecruiterDashboardPage from "./pages/recruiter/RecruiterDashboardPage";
import RecruiterJobsPage from "./pages/recruiter/RecruiterJobsPage";
import RecruiterJobDetailPage from "./pages/recruiter/RecruiterJobDetailPage";
import RecruiterCandidateDetailPage from "./pages/recruiter/RecruiterCandidateDetailPage";
import CandidateDashboardPage from "./pages/candidate/CandidateDashboardPage";
import CandidateJobsPage from "./pages/candidate/CandidateJobsPage";
import CandidateJobDetailPage from "./pages/candidate/CandidateJobDetailPage";
import CandidateApplicationsPage from "./pages/candidate/CandidateApplicationsPage";
import CandidateApplicationDetailPage from "./pages/candidate/CandidateApplicationDetailPage";
import NavBar from "./components/NavBar";
import PageHeader from "./components/PageHeader";
import SectionCard from "./components/SectionCard";
import StatCard from "./components/StatCard";
import RoleRoute from "./components/RoleRoute";
import { LoadingState } from "./components/UXStates";
import { getJobs } from "./api/jobs";
import { getResumes } from "./api/resumes";
import { getStoredRole } from "./api/authRole";
import type { components } from "./types/api";
import {
  IconBarChart,
  IconBriefcase,
  IconFileText,
  IconHistory,
  IconPlus,
  IconSparkles,
  IconWand,
} from "./components/icons";

type Job = components["schemas"]["JobResponse"];
type Resume = components["schemas"]["ResumeResponse"];

function Layout() {
  return (
    <>
      <NavBar />
      <Outlet />
    </>
  );
}

function MarketingHome() {
  return (
    <main>
      <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem" }}>
        <span
          className="app-topbar__brand-mark"
          style={{ margin: "0 auto 1.25rem" }}
        >
          <IconSparkles width={22} height={22} />
        </span>
        <h1>Recruitment Intelligence</h1>
        <p className="muted" style={{ maxWidth: "34rem", margin: "0 auto 1.5rem" }}>
          Screen, rank and evaluate candidates with AI-assisted matching —
          backed by explainable evidence for every decision.
        </p>
        <div
          style={{
            display: "flex",
            gap: "0.75rem",
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          <Link to="/login" className="btn btn-primary">
            Login to get started
          </Link>
          <Link to="/register" className="btn btn-secondary">
            Create an account
          </Link>
        </div>
      </div>
    </main>
  );
}

function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setLoading(false);
      return;
    }

    Promise.all([getJobs(token), getResumes(token)])
      .then(([jobsData, resumesData]) => {
        setJobs(jobsData);
        setResumes(resumesData);
      })
      .catch((err) => {
        console.error("Failed to load dashboard data:", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <main>
      <PageHeader
        eyebrow="Overview"
        title="Recruitment Intelligence"
        subtitle="Screen, rank and evaluate candidates with AI-assisted matching."
        actions={
          <>
            <Link to="/jobs" className="btn btn-primary">
              <IconPlus width={16} height={16} />
              Create Job
            </Link>
            <Link to="/resumes" className="btn btn-secondary">
              <IconPlus width={16} height={16} />
              Add Resume
            </Link>
            <Link to="/screening" className="btn btn-secondary">
              <IconWand width={16} height={16} />
              Start Screening
            </Link>
          </>
        }
      />

      {loading ? (
        <LoadingState message="Loading dashboard..." />
      ) : (
        <>
          <div className="grid-2" style={{ marginBottom: "1.5rem" }}>
            <StatCard
              icon={<IconBriefcase width={18} height={18} />}
              label="Active Jobs"
              value={jobs.length}
            />
            <StatCard
              icon={<IconFileText width={18} height={18} />}
              label="Candidate Resumes"
              value={resumes.length}
            />
          </div>

          <div className="grid-2">
            <SectionCard title="Recent Jobs">
              {jobs.length === 0 ? (
                <p className="muted">
                  No job descriptions have been created yet.
                </p>
              ) : (
                <ul className="stack" style={{ gap: "0.6rem" }}>
                  {jobs.slice(0, 5).map((job) => (
                    <li key={job.job_id}>
                      <strong>{job.title ?? job.job_id}</strong>
                      {job.location && (
                        <span className="muted"> — {job.location}</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
              <hr className="divider" />
              <Link to="/jobs">Manage jobs →</Link>
            </SectionCard>

            <SectionCard title="Quick Actions">
              <ul className="stack" style={{ gap: "0.6rem" }}>
                <li>
                  <Link to="/screening">
                    <IconWand
                      width={14}
                      height={14}
                      style={{ marginRight: "0.35rem" }}
                    />
                    Run a new screening
                  </Link>
                </li>
                <li>
                  <Link to="/ranking">
                    <IconBarChart
                      width={14}
                      height={14}
                      style={{ marginRight: "0.35rem" }}
                    />
                    View candidate rankings
                  </Link>
                </li>
                <li>
                  <Link to="/screening-history">
                    <IconHistory
                      width={14}
                      height={14}
                      style={{ marginRight: "0.35rem" }}
                    />
                    Review screening history
                  </Link>
                </li>
              </ul>
            </SectionCard>
          </div>
        </>
      )}
    </main>
  );
}

function HomePage() {
  const isAuthenticated = Boolean(
    localStorage.getItem("access_token"),
  );

  if (!isAuthenticated) {
    return <MarketingHome />;
  }

  if (getStoredRole() === "candidate") {
    return <Navigate to="/candidate/dashboard" replace />;
  }

  return <Dashboard />;
}

function NotFoundPage() {
  return (
    <main>
      <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem" }}>
        <h1>404</h1>
        <p>Page not found.</p>
        <Link to="/" className="btn btn-secondary">
          Back to home
        </Link>
      </div>
    </main>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />

        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route
          path="/register"
          element={<RegisterPage />}
        />

        <Route
          path="/jobs"
          element={<JobsPage />}
        />

        <Route
          path="/resumes"
          element={<ResumesPage />}
        />

        <Route
          path="/screening"
          element={<ScreeningPage />}
        />
       <Route
          path="/screening-history"
          element={<ScreeningHistoryPage />}
        />

        <Route
          path="/ranking"
          element={<RankingPage />}
        />

        <Route
          path="/ranking/:jobId/:resumeId"
          element={
              <CandidateMatchProfilePage />
          }
        />

        <Route
          path="/recruiter/dashboard"
          element={
            <RoleRoute allow={["admin", "recruiter"]}>
              <RecruiterDashboardPage />
            </RoleRoute>
          }
        />
        <Route
          path="/recruiter/jobs"
          element={
            <RoleRoute allow={["admin", "recruiter"]}>
              <RecruiterJobsPage />
            </RoleRoute>
          }
        />
        <Route
          path="/recruiter/jobs/:jobId"
          element={
            <RoleRoute allow={["admin", "recruiter"]}>
              <RecruiterJobDetailPage />
            </RoleRoute>
          }
        />
        <Route
          path="/recruiter/jobs/:jobId/candidates/:applicationId"
          element={
            <RoleRoute allow={["admin", "recruiter"]}>
              <RecruiterCandidateDetailPage />
            </RoleRoute>
          }
        />

        <Route
          path="/candidate/dashboard"
          element={
            <RoleRoute allow={["candidate"]}>
              <CandidateDashboardPage />
            </RoleRoute>
          }
        />
        <Route
          path="/candidate/jobs"
          element={
            <RoleRoute allow={["candidate"]}>
              <CandidateJobsPage />
            </RoleRoute>
          }
        />
        <Route
          path="/candidate/jobs/:jobId"
          element={
            <RoleRoute allow={["candidate"]}>
              <CandidateJobDetailPage />
            </RoleRoute>
          }
        />
        <Route
          path="/candidate/applications"
          element={
            <RoleRoute allow={["candidate"]}>
              <CandidateApplicationsPage />
            </RoleRoute>
          }
        />
        <Route
          path="/candidate/applications/:applicationId"
          element={
            <RoleRoute allow={["candidate"]}>
              <CandidateApplicationDetailPage />
            </RoleRoute>
          }
        />

        <Route
          path="/404"
          element={<NotFoundPage />}
        />

        <Route
          path="*"
          element={<Navigate to="/404" replace />}
        />
      </Route>
    </Routes>
  );
}
