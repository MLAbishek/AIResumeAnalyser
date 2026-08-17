import { Navigate, Route, Routes } from "react-router-dom";
import { useEffect } from "react";
import { checkHealth } from "./api";
import JobsPage from "./pages/JobsPage";
import LoginPage from "./pages/LoginPage";

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
  useEffect(() => {
    checkHealth()
      .then((data) => {
        console.log("Backend health:", data);
      })
      .catch((error) => {
        console.error("Backend health check failed:", error);
      });
  }, []);

  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/jobs" element={<JobsPage />} />
      <Route path="/404" element={<NotFoundPage />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}