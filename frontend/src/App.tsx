import { Navigate, Route, Routes } from "react-router-dom";
import JobsPage from "./pages/JobsPage";
import ResumesPage from "./pages/ResumesPage";
import ScreeningPage from "./pages/ScreeningPage";
import RankingPage from "./pages/RankingPage";
import CandidateMatchProfilePage from "./pages/CandidateMatchProfilePage";
import ScreeningHistoryPage from "./pages/ScreeningHistoryPage";

function HomePage() {
  return (
    <main>
      <h1>AI Resume Screening</h1>
      <p>Frontend foundation is ready.</p>
    </main>
  );
}

function NotFoundPage() {
  return (
    <main>
      <h1>404</h1>
      <p>Page not found.</p>
    </main>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />

      <Route
        path="/jobs"
        element={<JobsPage />}
      />

      <Route
        path="/resumes"
        element={<ResumesPage />}
      />

      <Route
        path="/screening"
        element={<ScreeningPage />}
      />
     <Route
        path="/screening-history"
        element={<ScreeningHistoryPage />}
      />

      <Route
        path="/ranking"
        element={<RankingPage />}
      />

      <Route
        path="/ranking/:jobId/:resumeId"
        element={
            <CandidateMatchProfilePage />
        }
      />
      <Route
        path="/404"
        element={<NotFoundPage />}
      />

      <Route
        path="*"
        element={<Navigate to="/404" replace />}
      />
    </Routes>
  );
}