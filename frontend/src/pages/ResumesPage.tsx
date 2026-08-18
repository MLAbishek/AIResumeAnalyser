import { useEffect, useState } from "react";
import { createResume, getResumes } from "../api/resumes";
import { getApiErrorMessage } from "../api/client";
import type { components } from "../types/api";
import PageHeader from "../components/PageHeader";
import SectionCard from "../components/SectionCard";
import SkillChip from "../components/SkillChip";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../components/UXStates";
import { IconPlus } from "../components/icons";

type Resume = components["schemas"]["ResumeResponse"];

function initials(name: string | null, fallback: string): string {
  const source = name?.trim() || fallback;
  const parts = source.split(/\s+/).filter(Boolean);

  if (parts.length === 0) {
    return "?";
  }

  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }

  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function ResumesPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(
    null,
  );

  const [resumeId, setResumeId] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [summary, setSummary] = useState("");
  const [skills, setSkills] = useState("");
  const [jobTitles, setJobTitles] = useState("");
  const [organizations, setOrganizations] = useState("");
  const [technologies, setTechnologies] = useState("");
  const [experienceMonths, setExperienceMonths] = useState(0);
  const [rawText, setRawText] = useState("");

  function loadResumes() {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    getResumes(token)
      .then((data) => {
        setResumes(data);
      })
      .catch((err) => {
        console.error("Failed to load resumes:", err);
        setError(
          getApiErrorMessage(err, "Failed to load resumes."),
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    loadResumes();
  }, []);

  function parseList(value: string): string[] {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  async function handleCreateResume(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const token = localStorage.getItem("access_token");

    if (!token) {
      setFormError("Authentication required.");
      return;
    }

    if (!resumeId.trim()) {
      setFormError("Resume ID is required.");
      return;
    }

    setCreating(true);
    setFormError(null);

    try {
      const created = await createResume(
        {
          resume_id: resumeId.trim(),
          name: name.trim() || undefined,
          email: email.trim() || undefined,
          phone: phone.trim() || undefined,
          summary: summary.trim() || undefined,

          skills: parseList(skills),
          job_titles: parseList(jobTitles),
          organizations: parseList(organizations),
          technologies: parseList(technologies),

          total_experience_months: experienceMonths,
          raw_text: rawText.trim() || undefined,

          experiences: [],
          education: [],
        },
        token,
      );

      setResumes((currentResumes) => [
        created,
        ...currentResumes,
      ]);

      setResumeId("");
      setName("");
      setEmail("");
      setPhone("");
      setSummary("");
      setSkills("");
      setJobTitles("");
      setOrganizations("");
      setTechnologies("");
      setExperienceMonths(0);
      setRawText("");
    } catch (err) {
      console.error("Failed to create resume:", err);
      setFormError(
        getApiErrorMessage(err, "Failed to create resume."),
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <main>
      <PageHeader
        eyebrow="Candidates"
        title="Candidate Resumes"
        subtitle="Manage candidate profiles used for AI screening."
      />

      <div className="workflow-layout">
        <div className="stack">
          <SectionCard title="Resumes">
            {loading && (
              <LoadingState message="Loading resumes..." />
            )}

            {error && (
              <ErrorState message={error} onRetry={loadResumes} />
            )}

            {!loading && !error && resumes.length === 0 && (
              <EmptyState
                title="No resumes yet"
                message="No candidate resumes have been added yet."
              />
            )}

            {!loading && resumes.length > 0 && (
              <ul className="stack" style={{ gap: "0.6rem" }}>
                {resumes.map((resume) => (
                  <li
                    key={resume.resume_id}
                    className="card"
                    style={{ margin: 0 }}
                  >
                    <div
                      style={{
                        display: "flex",
                        gap: "0.85rem",
                      }}
                    >
                      <span className="avatar">
                        {initials(
                          resume.name,
                          resume.resume_id,
                        )}
                      </span>

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <h3 className="mt-0" style={{ margin: 0 }}>
                          {resume.name ?? resume.resume_id}
                        </h3>

                        <p className="muted text-sm">
                          {resume.resume_id}
                          {resume.email
                            ? ` · ${resume.email}`
                            : ""}
                          {" · "}
                          {resume.total_experience_months} months
                          experience
                        </p>

                        {resume.skills.length > 0 && (
                          <div className="chip-row">
                            {resume.skills
                              .slice(0, 8)
                              .map((skill) => (
                                <SkillChip key={skill}>
                                  {skill}
                                </SkillChip>
                              ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>

        <div className="workflow-layout__aside">
          <SectionCard
            title="Add Resume"
            subtitle="Add a candidate profile for AI screening."
          >
            <form onSubmit={handleCreateResume}>
              <div className="field-group">
                <p className="field-group__title">Identity</p>

                <div className="field">
                  <label htmlFor="resume-id">Resume ID</label>
                  <input
                    id="resume-id"
                    name="resume_id"
                    value={resumeId}
                    onChange={(event) =>
                      setResumeId(event.target.value)
                    }
                    required
                  />
                </div>

                <div className="field">
                  <label htmlFor="resume-name">Name</label>
                  <input
                    id="resume-name"
                    name="name"
                    value={name}
                    onChange={(event) =>
                      setName(event.target.value)
                    }
                  />
                </div>

                <div className="form-grid">
                  <div className="field">
                    <label htmlFor="resume-email">
                      Email
                    </label>
                    <input
                      id="resume-email"
                      name="email"
                      type="email"
                      value={email}
                      onChange={(event) =>
                        setEmail(event.target.value)
                      }
                    />
                  </div>

                  <div className="field">
                    <label htmlFor="resume-phone">
                      Phone
                    </label>
                    <input
                      id="resume-phone"
                      name="phone"
                      value={phone}
                      onChange={(event) =>
                        setPhone(event.target.value)
                      }
                    />
                  </div>
                </div>

                <div className="field">
                  <label htmlFor="resume-summary">
                    Summary
                  </label>
                  <textarea
                    id="resume-summary"
                    name="summary"
                    value={summary}
                    onChange={(event) =>
                      setSummary(event.target.value)
                    }
                  />
                </div>
              </div>

              <div className="field-group">
                <p className="field-group__title">
                  Skills &amp; Experience
                </p>

                <div className="field">
                  <label htmlFor="resume-skills">
                    Skills
                  </label>
                  <input
                    id="resume-skills"
                    name="skills"
                    placeholder="React, TypeScript, Python"
                    value={skills}
                    onChange={(event) =>
                      setSkills(event.target.value)
                    }
                  />
                </div>

                <div className="field">
                  <label htmlFor="resume-job-titles">
                    Job Titles
                  </label>
                  <input
                    id="resume-job-titles"
                    name="job_titles"
                    placeholder="Software Engineer, Developer"
                    value={jobTitles}
                    onChange={(event) =>
                      setJobTitles(event.target.value)
                    }
                  />
                </div>

                <div className="field">
                  <label htmlFor="resume-organizations">
                    Organizations
                  </label>
                  <input
                    id="resume-organizations"
                    name="organizations"
                    placeholder="Google, Microsoft"
                    value={organizations}
                    onChange={(event) =>
                      setOrganizations(event.target.value)
                    }
                  />
                </div>

                <div className="field">
                  <label htmlFor="resume-technologies">
                    Technologies
                  </label>
                  <input
                    id="resume-technologies"
                    name="technologies"
                    placeholder="React, FastAPI, PostgreSQL"
                    value={technologies}
                    onChange={(event) =>
                      setTechnologies(event.target.value)
                    }
                  />
                </div>

                <div className="field">
                  <label htmlFor="resume-experience">
                    Total Experience (months)
                  </label>
                  <input
                    id="resume-experience"
                    name="total_experience_months"
                    type="number"
                    min="0"
                    value={experienceMonths}
                    onChange={(event) =>
                      setExperienceMonths(
                        Number(event.target.value),
                      )
                    }
                  />
                </div>
              </div>

              <div className="field-group">
                <p className="field-group__title">
                  Other
                </p>

                <div className="field">
                  <label htmlFor="resume-raw-text">
                    Raw Resume Text
                  </label>
                  <textarea
                    id="resume-raw-text"
                    name="raw_text"
                    value={rawText}
                    onChange={(event) =>
                      setRawText(event.target.value)
                    }
                    rows={8}
                  />
                </div>
              </div>

              {formError && (
                <p role="alert" className="validation-message">
                  {formError}
                </p>
              )}

              <button
                type="submit"
                className="btn btn-primary btn-block"
                disabled={creating}
              >
                {creating ? (
                  <span
                    className="spinner-inline"
                    aria-hidden="true"
                  />
                ) : (
                  <IconPlus width={16} height={16} />
                )}
                {creating ? "Creating..." : "Create Resume"}
              </button>
            </form>
          </SectionCard>
        </div>
      </div>
    </main>
  );
}
