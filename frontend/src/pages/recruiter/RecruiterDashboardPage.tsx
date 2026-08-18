import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getJobs, listJobApplications } from "../../api";
import PageHeader from "../../components/PageHeader";
import SectionCard from "../../components/SectionCard";
import StatCard from "../../components/StatCard";
import { LoadingState } from "../../components/UXStates";
import {
  IconBarChart,
  IconBriefcase,
  IconCheck,
  IconPlus,
} from "../../components/icons";
import type { components } from "../../types/api";

type Job = components["schemas"]["JobResponse"];

type JobWithCounts = Job & {
  applicationCount: number;
  shortlistedCount: number;
};

export default function RecruiterDashboardPage() {
  const [jobs, setJobs] = useState<JobWithCounts[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }

    getJobs(token)
      .then(async (data) => {
        const withCounts = await Promise.all(
          data.slice(0, 20).map(async (job) => {
            try {
              const applications = await listJobApplications(
                job.job_id,
                token,
              );
              return {
                ...job,
                applicationCount:
                  applications.total_applications,
                shortlistedCount:
                  applications.results.filter(
                    (r) => r.status === "shortlisted",
                  ).length,
              };
            } catch {
              return {
                ...job,
                applicationCount: 0,
                shortlistedCount: 0,
              };
            }
          }),
        );
        setJobs(withCounts);
      })
      .catch((err) => {
        console.error(
          "Failed to load recruiter dashboard:",
          err,
        );
      })
      .finally(() => setLoading(false));
  }, []);

  const openJobs = jobs.filter((j) => j.status === "open");
  const totalApplications = jobs.reduce(
    (sum, j) => sum + j.applicationCount,
    0,
  );
  const totalShortlisted = jobs.reduce(
    (sum, j) => sum + j.shortlistedCount,
    0,
  );

  return (
    <main>
      <PageHeader
        eyebrow="Recruiter"
        title="Recruiter Dashboard"
        subtitle="Manage job openings and review AI-ranked candidates."
        actions={
          <Link to="/recruiter/jobs" className="btn btn-primary">
            <IconPlus width={16} height={16} />
            Manage Jobs
          </Link>
        }
      />

      {loading ? (
        <LoadingState message="Loading dashboard..." />
      ) : (
        <>
          <div className="grid-3" style={{ marginBottom: "1.5rem" }}>
            <StatCard
              icon={<IconBriefcase width={18} height={18} />}
              label="Open Jobs"
              value={openJobs.length}
            />
            <StatCard
              icon={<IconBarChart width={18} height={18} />}
              label="Applications"
              value={totalApplications}
            />
            <StatCard
              icon={<IconCheck width={18} height={18} />}
              label="Shortlisted"
              value={totalShortlisted}
            />
          </div>

          <SectionCard title="Recent Job Openings">
            {jobs.length === 0 ? (
              <p className="muted">
                No job descriptions have been created yet.
              </p>
            ) : (
              <ul className="stack" style={{ gap: "0.6rem" }}>
                {jobs.slice(0, 8).map((job) => (
                  <li
                    key={job.job_id}
                    className="card"
                    style={{ margin: 0 }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        flexWrap: "wrap",
                        gap: "0.5rem",
                      }}
                    >
                      <div>
                        <Link
                          to={`/recruiter/jobs/${encodeURIComponent(
                            job.job_id,
                          )}`}
                        >
                          <strong>
                            {job.title ?? job.job_id}
                          </strong>
                        </Link>
                        <p className="muted text-sm mt-0">
                          {job.applicationCount} applicant
                          {job.applicationCount === 1
                            ? ""
                            : "s"}{" "}
                          ·{" "}
                          {job.status === "open"
                            ? "Open"
                            : "Closed"}
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </>
      )}
    </main>
  );
}
