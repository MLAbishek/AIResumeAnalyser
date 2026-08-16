export interface Candidate {
  id: string;
  name: string;
  overallScore: number;
  eligible: boolean;
  decision: "shortlist" | "review" | "reject";
}