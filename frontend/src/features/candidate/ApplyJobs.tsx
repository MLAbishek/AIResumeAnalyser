import { Search } from "lucide-react";
import { useMemo, useState } from "react";

const jobs = [
  {
    id: "job-ml-1",
    company: "Reveleer Digital Solutions India Pvt. Ltd",
    title: "Campus Hiring | 2027 Batch",
    location: "Chennai",
    salary: "11.8L",
    stipend: "40K",
    type: "Intern + Full Time",
    applyBy: "17 Aug 2026",
    dateOfVisit: "27 Aug 2026",
    status: "Open for Applications",
    applicants: 501,
  },
  {
    id: "job-be-2",
    company: "Thiran Technologies",
    title: "Internship-cum-Placement Program",
    location: "Bengaluru",
    salary: "-",
    stipend: "-",
    type: "Intern + Full Time",
    applyBy: "14 Aug 2026",
    dateOfVisit: "-",
    status: "Closed for Applications",
    applicants: 231,
  },
  {
    id: "job-cv-3",
    company: "Grundfos Pumps",
    title: "Paid Internship Opportunity",
    location: "Hyderabad",
    salary: "10L",
    stipend: "25K",
    type: "Intern Leads to Full Time",
    applyBy: "13 Aug 2026",
    dateOfVisit: "-",
    status: "Closed for Applications",
    applicants: 184,
  },
  {
    id: "job-fs-4",
    company: "WinWire",
    title: "Full Time Engineering Role",
    location: "Pune",
    salary: "8.4L",
    stipend: "50K",
    type: "Full Time",
    applyBy: "1 Aug 2026",
    dateOfVisit: "13 Aug 2026",
    status: "In Progress",
    applicants: 92,
  },
];

export default function ApplyJobs() {
  const [query, setQuery] = useState("");
  const [selectedJobId, setSelectedJobId] = useState(jobs[0].id);
  const [resumeFileName, setResumeFileName] = useState("");
  const [appliedJobs, setAppliedJobs] = useState<string[]>([]);

  const visibleJobs = useMemo(() => {
    const normalized = query.trim().toLowerCase();

    if (!normalized) {
      return jobs;
    }

    return jobs.filter((job) => {
      const haystack =
        `${job.company} ${job.title} ${job.location} ${job.type}`.toLowerCase();
      return haystack.includes(normalized);
    });
  }, [query]);

  const selectedJob =
    visibleJobs.find((job) => job.id === selectedJobId) ??
    visibleJobs[0] ??
    jobs[0];

  const isAlreadyApplied = appliedJobs.includes(selectedJob.id);

  const applyToJob = () => {
    if (!resumeFileName || isAlreadyApplied) {
      return;
    }

    if (!appliedJobs.includes(selectedJob.id)) {
      setAppliedJobs((previous) => [...previous, selectedJob.id]);
      setResumeFileName("");
    }
  };

  return (
    <div className="candidate-jobs-page">
      <div className="page-header">
        <div>
          <h1>Jobs</h1>
          <p>{visibleJobs.length} jobs listed</p>
        </div>

        <div className="jobs-search">
          <div className="search-shell">
            <select aria-label="company filter">
              <option>Company Name</option>
            </select>

            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by company, role or location..."
            />

            <button type="button" aria-label="search jobs">
              <Search size={18} />
            </button>
          </div>
        </div>
      </div>

      <div className="jobs-filters" aria-label="job filters">
        <button type="button">Apply By (Desc)</button>
        <button type="button">Job Type</button>
        <button type="button">Job Status</button>
        <button type="button">Date Of Visit</button>
      </div>

      <section className="panel jobs-table-panel">
        <div className="jobs-table-header">
          <span>Title</span>
          <span>Salary</span>
          <span>Stipend</span>
          <span>Apply Before</span>
          <span>Status</span>
        </div>

        {visibleJobs.map((job) => (
          <button
            type="button"
            className={`jobs-row ${job.id === selectedJob.id ? "active" : ""}`}
            key={job.id}
            onClick={() => setSelectedJobId(job.id)}
          >
            <div>
              <strong>{job.company}</strong>
              <span>{job.title}</span>
            </div>

            <span>{job.salary}</span>
            <span>{job.stipend}</span>
            <span>{job.applyBy}</span>
            <span
              className={`job-status ${job.status.toLowerCase().replace(/\s+/g, "-")}`}
            >
              {job.status}
            </span>
          </button>
        ))}
      </section>

      <section className="panel job-detail-panel">
        <div className="job-detail-top">
          <div>
            <h2>{selectedJob.company}</h2>
            <p>{selectedJob.title}</p>
          </div>

          <span
            className={`job-status ${selectedJob.status.toLowerCase().replace(/\s+/g, "-")}`}
          >
            {selectedJob.status}
          </span>
        </div>

        <div className="job-metadata">
          <span>{selectedJob.location}</span>
          <span>{selectedJob.type}</span>
          <span>Date of visit: {selectedJob.dateOfVisit}</span>
        </div>

        <div className="job-stats-grid">
          <article>
            <h3>{selectedJob.applicants}</h3>
            <p>Applicants</p>
          </article>
          <article>
            <h3>{selectedJob.salary}</h3>
            <p>CTC</p>
          </article>
          <article>
            <h3>{selectedJob.stipend}</h3>
            <p>Internship Stipend</p>
          </article>
          <article>
            <h3>{selectedJob.applyBy}</h3>
            <p>Apply by</p>
          </article>
        </div>

        <div className="apply-footer">
          <label className="resume-upload-inline">
            Upload Resume
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={(event) => {
                const file = event.target.files?.[0];
                setResumeFileName(file ? file.name : "");
              }}
            />
          </label>

          <div className="apply-footer-actions">
            <span>
              {resumeFileName
                ? `Selected: ${resumeFileName}`
                : "No resume selected"}
            </span>

            <button
              className="primary-button"
              type="button"
              onClick={applyToJob}
              disabled={!resumeFileName || isAlreadyApplied}
            >
              {isAlreadyApplied ? "Applied" : "Apply with Resume"}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
