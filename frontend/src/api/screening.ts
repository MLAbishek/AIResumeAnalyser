import { apiRequest } from "./client";
import type { components } from "../types/api";

type JobResponse = components["schemas"]["JobResponse"];
type ResumeResponse = components["schemas"]["ResumeResponse"];

type ScreeningRequest =
  components["schemas"]["ScreeningRequest"];

type ScreeningResponse =
  components["schemas"]["ScreeningResponse"];

type JobDescription =
  components["schemas"]["JobDescription"];

type ScreeningResume =
  components["schemas"]["Resume"];

function buildJobDescription(
  job: JobResponse,
): JobDescription {
  return {
    job_id: job.job_id,
    title: job.title ?? null,
    summary: job.description ?? null,
    required_skills: job.required_skills ?? [],
    preferred_skills: job.preferred_skills ?? [],
    required_experience_years:
      job.required_experience_months != null
        ? job.required_experience_months / 12
        : null,
    education: [],
    certifications: [],
    responsibilities: [],
    location: job.location ?? null,
    job_type: job.job_type ?? null,
    raw_text: job.raw_text,
  };
}

function buildScreeningResume(
  resume: ResumeResponse,
): ScreeningResume {
  return {
    resume_id: resume.resume_id,
    name: resume.name ?? null,
    summary: resume.summary ?? null,
    skills: resume.skills ?? [],
    experience: resume.experiences.map(
      (experience) => ({
        role: experience.job_title,
        company: experience.company,
        start_date: experience.start_date,
        end_date: experience.end_date,
      }),
    ),
    education: resume.education.map(
      (education) => ({
        degree: education.degree,
        institution: education.institution,
        field: education.field_of_study ?? null,
        start_date: education.start_date ?? null,
        end_date: education.end_date ?? null,
      }),
    ),
    certifications: [],
    projects: [],
    job_titles: resume.job_titles ?? [],
    total_experience_years:
      resume.total_experience_months / 12,
    raw_text: resume.raw_text ?? "",
  };
}

export function screenCandidates(
  job: JobResponse,
  resumes: ResumeResponse[],
  token: string,
) {
  const request: ScreeningRequest = {
    job_description:
      buildJobDescription(job),

    resumes: resumes.map(
      buildScreeningResume,
    ),
  };

  return apiRequest<ScreeningResponse>(
    "/api/screen",
    {
      method: "POST",
      token,
      body: JSON.stringify(request),
    },
  );
}
