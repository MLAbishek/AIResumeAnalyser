import { BriefcaseBusiness, CheckCircle2, FileText, Users } from "lucide-react";

const statistics = [
  {
    title: "Total Resumes",
    value: "1,248",
    icon: FileText,
  },
  {
    title: "Active Jobs",
    value: "37",
    icon: BriefcaseBusiness,
  },
  {
    title: "Candidates Screened",
    value: "4,821",
    icon: Users,
  },
  {
    title: "Shortlisted",
    value: "684",
    icon: CheckCircle2,
  },
];

export default function Dashboard() {
  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Overview of your resume screening activity.</p>
        </div>
      </div>

      <div className="stats-grid">
        {statistics.map((stat) => {
          const Icon = stat.icon;

          return (
            <div className="stat-card" key={stat.title}>
              <div className="stat-icon">
                <Icon size={22} />
              </div>

              <div>
                <p>{stat.title}</p>
                <h2>{stat.value}</h2>
              </div>
            </div>
          );
        })}
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-header">
            <h2>Recent Screening Runs</h2>
          </div>

          <div className="screening-list">
            <div className="screening-row">
              <div>
                <strong>Machine Learning Engineer</strong>
                <span>842 resumes</span>
              </div>

              <span className="status completed">Completed</span>
            </div>

            <div className="screening-row">
              <div>
                <strong>Backend Engineer</strong>
                <span>421 resumes</span>
              </div>

              <span className="status processing">Processing</span>
            </div>

            <div className="screening-row">
              <div>
                <strong>Computer Vision Engineer</strong>
                <span>126 resumes</span>
              </div>

              <span className="status completed">Completed</span>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Screening Summary</h2>
          </div>

          <div className="summary-item">
            <span>Eligible</span>
            <strong>72%</strong>
          </div>

          <div className="summary-item">
            <span>Shortlisted</span>
            <strong>14%</strong>
          </div>

          <div className="summary-item">
            <span>Rejected</span>
            <strong>28%</strong>
          </div>
        </section>
      </div>
    </div>
  );
}
