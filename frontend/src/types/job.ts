export interface Job {
  id: string;
  title: string;
  company?: string;
  createdAt: string;
  status: "active" | "archived";
}