import { useEffect, useState } from "react";
import { createResume, getResumes } from "../api/resumes";
import type { components } from "../types/api";

type Resume = components["schemas"]["ResumeResponse"];

export default function ResumesPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    getResumes(token)
      .then((data) => {
        setResumes(data);
      })
      .catch((err) => {
        console.error("Failed to load resumes:", err);
        setError("Failed to load resumes.");
      })
      .finally(() => {
        setLoading(false);
      });
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
      setError("Authentication required.");
      return;
    }

    if (!resumeId.trim()) {
      setError("Resume ID is required.");
      return;
    }

    setCreating(true);
    setError(null);

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
      setError("Failed to create resume.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <main>
      <h1>Resume Management</h1>

      <section>
        <h2>Create Resume</h2>

        <form onSubmit={handleCreateResume}>
          <div>
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

          <div>
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

          <div>
            <label htmlFor="resume-email">Email</label>
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

          <div>
            <label htmlFor="resume-phone">Phone</label>
            <input
              id="resume-phone"
              name="phone"
              value={phone}
              onChange={(event) =>
                setPhone(event.target.value)
              }
            />
          </div>

          <div>
            <label htmlFor="resume-summary">Summary</label>
            <textarea
              id="resume-summary"
              name="summary"
              value={summary}
              onChange={(event) =>
                setSummary(event.target.value)
              }
            />
          </div>

          <div>
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

          <div>
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

          <div>
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

          <div>
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

          <div>
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

          <div>
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
              rows={10}
            />
          </div>

          {error && <p>{error}</p>}

          <button type="submit" disabled={creating}>
            {creating ? "Creating..." : "Create Resume"}
          </button>
        </form>
      </section>

      <section>
        <h2>Resumes</h2>

        {loading && <p>Loading resumes...</p>}

        {!loading && !error && resumes.length === 0 && (
          <p>No resumes available.</p>
        )}

        {!loading && resumes.length > 0 && (
          <ul>
            {resumes.map((resume) => (
              <li key={resume.resume_id}>
                <article>
                  <h3>
                    {resume.name ?? resume.resume_id}
                  </h3>

                  <p>
                    <strong>Resume ID:</strong>{" "}
                    {resume.resume_id}
                  </p>

                  {resume.email && (
                    <p>
                      <strong>Email:</strong>{" "}
                      {resume.email}
                    </p>
                  )}

                  {resume.phone && (
                    <p>
                      <strong>Phone:</strong>{" "}
                      {resume.phone}
                    </p>
                  )}

                  <p>
                    <strong>Experience:</strong>{" "}
                    {resume.total_experience_months} months
                  </p>

                  {resume.skills.length > 0 && (
                    <p>
                      <strong>Skills:</strong>{" "}
                      {resume.skills.join(", ")}
                    </p>
                  )}

                  {resume.job_titles.length > 0 && (
                    <p>
                      <strong>Job Titles:</strong>{" "}
                      {resume.job_titles.join(", ")}
                    </p>
                  )}

                  {resume.technologies.length > 0 && (
                    <p>
                      <strong>Technologies:</strong>{" "}
                      {resume.technologies.join(", ")}
                    </p>
                  )}

                  {resume.summary && (
                    <p>
                      <strong>Summary:</strong>{" "}
                      {resume.summary}
                    </p>
                  )}
                </article>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}