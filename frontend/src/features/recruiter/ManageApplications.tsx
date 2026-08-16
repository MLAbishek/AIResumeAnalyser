import { useState } from "react";

type ApplicationStatus = "New" | "Shortlisted" | "Rejected";

interface Application {
  id: string;
  name: string;
  role: string;
  status: ApplicationStatus;
}

const seedApplications: Application[] = [
  {
    id: "app-1",
    name: "Aarav Sharma",
    role: "Backend Engineer",
    status: "New",
  },
  {
    id: "app-2",
    name: "Mia Thomas",
    role: "Machine Learning Engineer",
    status: "Shortlisted",
  },
  {
    id: "app-3",
    name: "Ishita Rao",
    role: "Computer Vision Engineer",
    status: "New",
  },
];

export default function ManageApplications() {
  const [applications, setApplications] =
    useState<Application[]>(seedApplications);

  const updateStatus = (id: string, status: ApplicationStatus) => {
    setApplications((previous) =>
      previous.map((application) =>
        application.id === id ? { ...application, status } : application,
      ),
    );
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Manage Applications</h1>
          <p>Review candidate applications and update statuses.</p>
        </div>
      </div>

      <div className="panel">
        {applications.map((application) => (
          <div className="list-row" key={application.id}>
            <div>
              <strong>{application.name}</strong>
              <span>{application.role}</span>
            </div>

            <select
              value={application.status}
              onChange={(event) =>
                updateStatus(
                  application.id,
                  event.target.value as ApplicationStatus,
                )
              }
            >
              <option value="New">New</option>
              <option value="Shortlisted">Shortlisted</option>
              <option value="Rejected">Rejected</option>
            </select>
          </div>
        ))}
      </div>
    </div>
  );
}
