export interface Resume {
  id: string;
  filename: string;
  candidateName?: string;
  uploadedAt: string;
  status: "uploaded" | "processing" | "processed" | "failed";
}