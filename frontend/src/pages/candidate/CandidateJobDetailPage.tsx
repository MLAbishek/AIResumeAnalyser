import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  applyToJob,
  getAvailableJob,
  listMyApplications,
  listMyResumes,
  previewMatch,
  uploadResume,
} from "../../api";
import { getApiErrorMessage } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import SectionCard from "../../components/SectionCard";
import SkillChip from "../../components/SkillChip";
import FeedbackPanel from "../../components/FeedbackPanel";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../../components/UXStates";
import { IconWand } from "../../components/icons";
import type {
  CandidateJobDetail,
  ResumeResponse,
  ScreeningResultResponse,
} from "../../api/candidateJobs";

const SUPPORTED_FORMATS = ".pdf,.docx,.txt";

export default function CandidateJobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [job, setJob] = useState<CandidateJobDetail | null>(
    null,
  );
  const [resumes, setResumes] = useState<ResumeResponse[]>(
    [],
  );
  const [selectedResumeId, setSelectedResumeId] =
    useState("");
  const [existingApplicationId, setExistingApplicationId] =
    useState<number | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<
    string | null
  >(null);

  const [previewing, setPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState<
    string | null
  >(null);
  const [preview, setPreview] =
    useState<ScreeningResultResponse | null>(null);

  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState<
    string | null
  >(null);

  function load() {
    const token = localStorage.getItem("access_token");
    if (!token || !jobId) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    Promise.all([
      getAvailableJob(jobId, token),
      listMyResumes(token),
      listMyApplications(token),
    ])
      .then(([jobData, resumesData, applications]) => {
        setJob(jobData);
        setResumes(resumesData);

        if (resumesData.length > 0) {
          setSelectedResumeId(resumesData[0].resume_id);
        }

        const existing = applications.find(
          (app) => app.job_id === jobId,
        );

        if (existing) {
          setExistingApplicationId(
            existing.application_id,
          );
        }
      })
      .catch((err) => {
        console.error("Failed to load job:", err);
        setError(
          getApiErrorMessage(
            err,
            "Failed to load this job.",
          ),
        );
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, [jobId]);

  async function handleUpload(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];
    if (!file) return;

    const token = localStorage.getItem("access_token");
    if (!token) return;

    setUploading(true);
    setUploadError(null);
    setPreview(null);

    try {
      const resume = await uploadResume(file, token);
      setResumes((current) => [
        resume,
        ...current.filter(
          (r) => r.resume_id !== resume.resume_id,
        ),
      ]);
      setSelectedResumeId(resume.resume_id);
    } catch (err) {
      console.error("Resume upload failed:", err);
      setUploadError(
        getApiErrorMessage(
          err,
          "Resume could not be uploaded. Please try a PDF, DOCX, or TXT file.",
        ),
      );
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function handlePreview() {
    const token = localStorage.getItem("access_token");
    if (!token || !jobId || !selectedResumeId) return;

    setPreviewing(true);
    setPreviewError(null);

    try {
      const result = await previewMatch(
        jobId,
        selectedResumeId,
        token,
      );
      setPreview(result);
    } catch (err) {
      console.error("Match preview failed:", err);
      setPreviewError(
        getApiErrorMessage(
          err,
          "Failed to generate a match preview.",
        ),
      );
    } finally {
      setPreviewing(false);
    }
  }

  async function handleApply() {
    const token = localStorage.getItem("access_token");
    if (!token || !jobId || !selectedResumeId) return;

    setApplying(true);
    setApplyError(null);

    try {
      const application = await applyToJob(
        jobId,
        selectedResumeId,
        token,
      );
      navigate(
        `/candidate/applications/${application.application_id}`,
      );
    } catch (err) {
      console.error("Application failed:", err);
      setApplyError(
        getApiErrorMessage(
          err,
          "Failed to submit your application.",
        ),
      );
    } finally {
      setApplying(false);
    }
  }

  if (loading) {
    return (
      <main>
        <PageHeader eyebrow="Candidate" title="Job Details" />
        <LoadingState message="Loading job details..." />
      </main>
    );
  }

  if (error || !job) {
    return (
      <main>
        <PageHeader eyebrow="Candidate" title="Job Details" />
        <ErrorState
          message={error ?? "Job not found."}
          onRetry={load}
        />
        <Link to="/candidate/jobs">Back to Jobs</Link>
      </main>
    );
  }

  return (
    <main>
      <Link
        to="/candidate/jobs"
        className="btn btn-ghost"
        style={{ marginBottom: "1rem" }}
      >
        ← Back to Jobs
      </Link>

      <PageHeader
        eyebrow="Candidate"
        title={job.title ?? job.job_id}
        subtitle={`${job.location ?? "Location not specified"} · ${
          job.required_experience_months
        }+ months experience`}
      />

      <div className="workflow-layout">
        <div className="stack">
          <SectionCard title="Job Description">
            <p style={{ whiteSpace: "pre-wrap" }}>
              {job.description ?? job.raw_text}
            </p>

            {job.required_skills.length > 0 && (
              <>
                <p className="stat-card__label">
                  Required Skills
                </p>
                <div className="chip-row">
                  {job.required_skills.map((skill) => (
                    <SkillChip key={skill}>
                      {skill}
                    </SkillChip>
                  ))}
                </div>
              </>
            )}
          </SectionCard>

          {preview && (
            <FeedbackPanel screening={preview} />
          )}
        </div>

        <div className="workflow-layout__aside">
          {existingApplicationId ? (
            <SectionCard title="You've Applied">
              <p className="muted">
                You have already applied to this job.
              </p>
              <Link
                to={`/candidate/applications/${existingApplicationId}`}
                className="btn btn-primary btn-block"
              >
                View Application
              </Link>
            </SectionCard>
          ) : job.status !== "open" ? (
            <SectionCard title="Applications Closed">
              <EmptyState
                title="This job is no longer accepting applications"
                message="Check the available jobs list for other open roles."
              />
            </SectionCard>
          ) : (
            <>
              <SectionCard title="Upload Resume">
                <p className="field-hint">
                  Supported formats: PDF, DOCX, TXT.
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  aria-label="Upload Resume"
                  accept={SUPPORTED_FORMATS}
                  onChange={handleUpload}
                  disabled={uploading}
                />
                {uploading && (
                  <p className="muted text-sm">
                    <span
                      className="spinner-inline"
                      aria-hidden="true"
                      style={{ marginRight: "0.4rem" }}
                    />
                    Parsing resume...
                  </p>
                )}
                {uploadError && (
                  <p
                    role="alert"
                    className="validation-message"
                  >
                    {uploadError}
                  </p>
                )}

                {resumes.length > 0 && (
                  <div className="field">
                    <label htmlFor="resume-select">
                      Use Resume
                    </label>
                    <select
                      id="resume-select"
                      value={selectedResumeId}
                      onChange={(e) => {
                        setSelectedResumeId(e.target.value);
                        setPreview(null);
                      }}
                    >
                      {resumes.map((resume) => (
                        <option
                          key={resume.resume_id}
                          value={resume.resume_id}
                        >
                          {resume.name ?? resume.resume_id}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </SectionCard>

              <SectionCard title="Match Preview">
                <button
                  type="button"
                  className="btn btn-secondary btn-block"
                  disabled={
                    !selectedResumeId || previewing
                  }
                  onClick={handlePreview}
                  style={{ marginBottom: "0.75rem" }}
                >
                  {previewing ? (
                    <span
                      className="spinner-inline"
                      aria-hidden="true"
                    />
                  ) : (
                    <IconWand
                      width={16}
                      height={16}
                    />
                  )}
                  {previewing
                    ? "Analyzing..."
                    : "Preview Match Score"}
                </button>

                {previewError && (
                  <p
                    role="alert"
                    className="validation-message"
                  >
                    {previewError}
                  </p>
                )}

                <button
                  type="button"
                  className="btn btn-primary btn-block"
                  disabled={
                    !selectedResumeId || applying
                  }
                  onClick={handleApply}
                >
                  {applying && (
                    <span
                      className="spinner-inline"
                      aria-hidden="true"
                    />
                  )}
                  {applying ? "Applying..." : "Apply Now"}
                </button>

                {applyError && (
                  <p
                    role="alert"
                    className="validation-message"
                  >
                    {applyError}
                  </p>
                )}
              </SectionCard>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
