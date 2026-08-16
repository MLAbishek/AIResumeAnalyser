import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../app/auth";

interface JobDetailsProps {
  company: string;
  title: string;
  location: string;
  salary: string;
  stipend: string;
  type: string;
  applyBy: string;
  dateOfVisit: string;
  status: string;
  applicants: number;
  description: string;
  responsibilities: string[];
  skills: string[];
  benefits: string[];
}

export default function JobDetailsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  // Parse job id from URL query parameter
  const params = new URLSearchParams(location.search);
  const jobId = params.get("id");

  const [job, setJob] = useState<JobDetailsProps | null>(null);
  const [loading, setLoading] = useState(true);

  // Mock data based on jobId - in real app this would fetch from API
  useEffect(() => {
    if (!jobId) {
      setJob(null);
      setLoading(false);
      return;
    }

    // Mock mapping of job ids to details
    const mockJobs: Record<string, JobDetailsProps> = {
      "job-ml-1": {
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
        description:
          "Join our campus hiring program for 2027 batch graduates. This is a full-time role with mentorship opportunities.",
        responsibilities: [
          "Assist in developing digital solutions",
          "Collaborate with senior engineers",
          "Participate in code reviews",
        ],
        skills: ["JavaScript", "React", "Node.js", "Problem Solving"],
        benefits: [
          "Mentorship program",
          "Exposure to real projects",
          "Certificate of completion",
        ],
      },
      "job-be-2": {
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
        description:
          "Participate in our internship-cum-placement program to gain hands-on experience.",
        responsibilities: [
          "Support development tasks",
          "Attend team meetings",
          "Contribute to documentation",
        ],
        skills: ["Teamwork", "Communication", "Basic Coding"],
        benefits: ["Certificate", "Potential full-time offer"],
      },
      "job-cv-3": {
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
        description:
          "Join our paid internship program in our Hyderabad office.",
        responsibilities: [
          "Assist senior engineers",
          "Test mechanical systems",
          "Support maintenance tasks",
        ],
        skills: ["Mechanical Systems", "Testing", "Maintenance"],
        benefits: ["Stipend", "Potential full-time role"],
      },
      "job-fs-4": {
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
        description:
          "Full-time engineering position with growth opportunities.",
        responsibilities: [
          "Develop software features",
          "Participate in agile ceremonies",
          "Collaborate with cross-functional teams",
        ],
        skills: ["Software Development", "Agile Methodologies"],
        benefits: [
          "Competitive salary",
          "Health benefits",
          "Growth opportunities",
        ],
      },
    };

    const job = mockJobs[jobId];
    setJob(job);
    setLoading(false);
  }, [jobId]);

  if (loading || !job) {
    return <div className="job-details-loading">Loading job details...</div>;
  }

  const handleBack = () => {
    navigate(-1);
  };

  return (
    <div className="job-details-page">
      <div className="back-navigation">
        <button onClick={closeBackNavigation} className="back-button">
          ← Back
        </button>
      </div>
      <div className="job-details-container">
        <div className="job-header">
          <h1>{job.title}</h1>
          <span
            className={`job-status ${job.status.toLowerCase().replace(/\s+/g, "-")}`}
          >
            {job.status}
          </span>
        </div>
        <div className="job-meta">
          <div className="meta-grid">
            <div>
              <strong>Company:</strong> {job.company}
            </div>
            <div>
              <strong>Location:</strong> {job.location}
            </div>
            <div>
              <strong>Type:</strong> {job.type}
            </div>
          </div>
        </div>
        <div className="job-details">
          <div className="meta-section">
            <h2>Compensation</h2>
            <div>
              <strong>Salary:</strong> {job.salary}
            </div>
            <div>
              <strong>Stipend:</strong> {job.stipend}
            </div>
            <div>
              <strong>Apply By:</strong> {job.applyBy}
            </div>
          </div>
          <div className="meta-section">
            <h2>Opportunity Details</h2>
            <div>
              <strong>Applicants:</strong> {job.applicants}
            </div>
            <div>
              <strong>Status:</strong> {job.status}
            </div>
          </div>
        </div>
        <div className="job-description">
          <h2>About the Role</h2>
          <p>{job.description}</p>
        </div>
        <div className="job-responsibilities">
          <h2>Key Responsibilities</h2>
          <ul>
            {job.responsibilities.map((responsibility, index) => (
              <li key={index}>{responsibility}</li>
            ))}
          </ul>
        </div>
        <div className="job-skills">
          <h2>Required Skills</h2>
          <ul>
            {job.skills.map((skill, index) => (
              <li key={index}>{skill}</li>
            ))}
          </ul>
        </div>
        <div className="job-benefits">
          <h2>What You'll Gain</h2>
          <ul>
            {job.benefits.map((benefit, index) => (
              <li key={index}>{benefit}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function closeBackNavigation() {
  window.history.back();
}
