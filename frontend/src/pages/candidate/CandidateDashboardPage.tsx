import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listAvailableJobs, listMyApplications } from "../../api";
import PageHeader from "../../components/PageHeader";
import SectionCard from "../../components/SectionCard";
import StatCard from "../../components/StatCard";
import { DecisionBadge } from "../../components/StatusBadge";
import { LoadingState } from "../../components/UXStates";
import {
  IconBarChart,
  IconBriefcase,
  IconWand,
} from "../../components/icons";
import type { CandidateJobSummary } from "../../api/candidateJobs";
import type { ApplicationResponse } from "../../api/candidateJobs";

export default function CandidateDashboardPage() {
  const [jobs, setJobs] = useState<CandidateJobSummary[]>([]);
  const [applications, setApplications] = useState<
    ApplicationResponse[]
  >([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }

    Promise.all([
      listAvailableJobs(token),
      listMyApplications(token),
    ])
      .then(([jobsData, applicationsData]) => {
        setJobs(jobsData);
        setApplications(applicationsData);
      })
      .catch((err) => {
        console.error(
          "Failed to load candidate dashboard:",
          err,
        );
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <main>
      <PageHeader
        eyebrow="Find your next opportunity"
        title="Candidate Dashboard"
        subtitle="Browse open roles and track your applications."
        actions={
          <Link to="/candidate/jobs" className="btn btn-primary">
            <IconBriefcase width={16} height={16} />
            Browse Jobs
          </Link>
        }
      />

      {loading ? (
        <LoadingState message="Loading dashboard..." />
      ) : (
        <>
          <div className="grid-2" style={{ marginBottom: "1.5rem" }}>
            <StatCard
              icon={<IconBriefcase width={18} height={18} />}
              label="Available Jobs"
              value={jobs.length}
            />
            <StatCard
              icon={<IconWand width={18} height={18} />}
              label="My Applications"
              value={applications.length}
            />
          </div>

          <div className="grid-2">
            <SectionCard title="Available Jobs">
              {jobs.length === 0 ? (
                <p className="muted">
                  No job openings are available right now.
                </p>
              ) : (
                <ul className="stack" style={{ gap: "0.6rem" }}>
                  {jobs.slice(0, 5).map((job) => (
                    <li key={job.job_id}>
                      <Link
                        to={`/candidate/jobs/${encodeURIComponent(
                          job.job_id,
                        )}`}
                      >
                        <strong>
                          {job.title ?? job.job_id}
                        </strong>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
              <hr className="divider" />
              <Link to="/candidate/jobs">
                Browse all jobs →
              </Link>
            </SectionCard>

            <SectionCard title="My Applications">
              {applications.length === 0 ? (
                <p className="muted">
                  You haven&apos;t applied to any jobs yet.
                </p>
              ) : (
                <ul className="stack" style={{ gap: "0.6rem" }}>
                  {applications.slice(0, 5).map((app) => (
                    <li
                      key={app.application_id}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <Link
                        to={`/candidate/applications/${app.application_id}`}
                      >
                        {app.job_title ?? app.job_id}
                      </Link>
                      <DecisionBadge decision={app.status} />
                    </li>
                  ))}
                </ul>
              )}
              <hr className="divider" />
              <Link to="/candidate/applications">
                <IconBarChart
                  width={14}
                  height={14}
                  style={{ marginRight: "0.35rem" }}
                />
                View all applications →
              </Link>
            </SectionCard>
          </div>
        </>
      )}
    </main>
  );
}
