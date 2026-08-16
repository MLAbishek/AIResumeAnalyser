import type { Resume } from "../types/resume";

export const mockResumes: Resume[] = [
  {
    id: "resume-001",
    filename: "john-doe.pdf",
    candidateName: "John Doe",
    uploadedAt: "2026-08-16T10:00:00Z",
    status: "processed",
  },
  {
    id: "resume-002",
    filename: "sarah-smith.pdf",
    candidateName: "Sarah Smith",
    uploadedAt: "2026-08-16T10:10:00Z",
    status: "processed",
  },
  {
    id: "resume-003",
    filename: "alex-kumar.pdf",
    candidateName: "Alex Kumar",
    uploadedAt: "2026-08-16T10:20:00Z",
    status: "processing",
  },
];