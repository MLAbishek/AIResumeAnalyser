import { mockResumes } from "../mocks/resumes";
import type { Resume } from "../types/resume";

export const resumeService = {
  async getResumes(): Promise<Resume[]> {
    await new Promise((resolve) => setTimeout(resolve, 500));

    return mockResumes;
  },

  async getResume(id: string): Promise<Resume | undefined> {
    await new Promise((resolve) => setTimeout(resolve, 300));

    return mockResumes.find((resume) => resume.id === id);
  },
};