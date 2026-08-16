import { useState, type FormEvent } from "react";

interface JobDraft {
  title: string;
  location: string;
}

export default function CreateJob() {
  const [draft, setDraft] = useState<JobDraft>({ title: "", location: "" });
  const [jobs, setJobs] = useState<JobDraft[]>([]);

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!draft.title.trim() || !draft.location.trim()) {
      return;
    }

    setJobs((previous) => [draft, ...previous]);
    setDraft({ title: "", location: "" });
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Create Job</h1>
          <p>Create new openings and publish them to candidates.</p>
        </div>
      </div>

      <form className="panel form-panel" onSubmit={onSubmit}>
        <label>
          Job Title
          <input
            type="text"
            value={draft.title}
            onChange={(event) =>
              setDraft((previous) => ({
                ...previous,
                title: event.target.value,
              }))
            }
            placeholder="e.g., Senior Data Engineer"
            required
          />
        </label>

        <label>
          Location
          <input
            type="text"
            value={draft.location}
            onChange={(event) =>
              setDraft((previous) => ({
                ...previous,
                location: event.target.value,
              }))
            }
            placeholder="e.g., Pune"
            required
          />
        </label>

        <button className="primary-button" type="submit">
          Create Job
        </button>
      </form>

      <div className="panel" style={{ marginTop: 20 }}>
        {jobs.length === 0 ? (
          <div className="empty-state">No jobs created in this session.</div>
        ) : (
          jobs.map((job) => (
            <div className="list-row" key={`${job.title}-${job.location}`}>
              <div>
                <strong>{job.title}</strong>
                <span>{job.location}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
