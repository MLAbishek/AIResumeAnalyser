import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

// This is the master end-to-end journey for the two-sided
// recruitment platform: a recruiter creates a job, a candidate
// discovers it, uploads a real resume, gets a real AI match score
// from the existing screening pipeline, applies, and the recruiter
// reviews and acts on that application - then the candidate sees
// the resulting status and feedback. Every step exercises the real
// backend (auth, database, AI pipeline) - nothing here is mocked.
//
// Uses fresh, unique accounts every run (via Date.now()) and never
// touches the shared frontend-test@example.com account used by the
// other E2E/integration tests.

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const RESUME_FIXTURE = path.join(
  __dirname,
  "fixtures",
  "sample-resume.txt",
);

// Generous budget: this journey chains two real registrations,
// two real logins, a real file upload + AI pipeline run, and a
// recruiter review - each step hits the real backend. When this is
// the first test to run against a freshly-started dev server, Vite
// also has to compile the recruiter/candidate route modules on
// first visit.
test.setTimeout(180000);

test("recruiter creates a job, a candidate applies with a real AI match score, and the recruiter reviews and shortlists them", async ({
  page,
}) => {
  const ts = Date.now();
  const recruiterEmail = `journey-recruiter-${ts}@example.com`;
  const candidateEmail = `journey-candidate-${ts}@example.com`;
  const password = "StrongPassword123!";
  const jobTitle = `Frontend Engineer ${ts}`;
  const candidateName = "Taylor Morgan";

  // ---------------------------------------------------------
  // RECRUITER: register, log in, create a job
  // ---------------------------------------------------------

  await page.goto("/register");
  await page
    .getByRole("radio", { name: "Recruiter" })
    .click();
  await page.getByLabel("Email").fill(recruiterEmail);
  await page
    .getByLabel("Password", { exact: true })
    .fill(password);
  await page
    .getByLabel("Confirm Password")
    .fill(password);
  await page
    .getByRole("button", { name: "Create Account" })
    .click();

  await page.waitForURL("**/login");
  await page.getByLabel("Email").fill(recruiterEmail);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL("**/jobs");

  await page.goto("/recruiter/jobs");
  await page.getByLabel("Job Title").fill(jobTitle);
  await page
    .locator("#recruiter-job-skills")
    .fill("React, TypeScript");
  await page
    .locator("#recruiter-job-experience")
    .fill("12");
  await page
    .locator("#recruiter-job-raw-text")
    .fill(
      "Frontend Engineer with React and TypeScript experience. 12 months minimum.",
    );
  await page
    .getByRole("button", { name: "Create Job" })
    .click();

  await expect(
    page.getByRole("link", { name: jobTitle }),
  ).toBeVisible({ timeout: 15000 });

  // ---------------------------------------------------------
  // CANDIDATE: register, log in, discover the job
  // ---------------------------------------------------------

  await page.goto("/register");
  await page
    .getByRole("radio", { name: "Candidate" })
    .click();
  await page.getByLabel("Email").fill(candidateEmail);
  await page
    .getByLabel("Password", { exact: true })
    .fill(password);
  await page
    .getByLabel("Confirm Password")
    .fill(password);
  await page
    .getByRole("button", { name: "Create Account" })
    .click();

  await page.waitForURL("**/login");
  await page.getByLabel("Email").fill(candidateEmail);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Login" }).click();

  // Candidates land in their own portal, not /jobs.
  await page.waitForURL("**/candidate/dashboard", { timeout: 60000 });

  await page.goto("/candidate/jobs");
  await page
    .getByRole("link", { name: "View Job" })
    .first()
    .waitFor();

  await page.getByLabel("Search jobs").fill(jobTitle);
  await page
    .getByRole("link", { name: "View Job" })
    .first()
    .click();

  await expect(
    page.getByRole("heading", { name: jobTitle }),
  ).toBeVisible();

  // ---------------------------------------------------------
  // CANDIDATE: upload a real resume, get a real match score
  // ---------------------------------------------------------

  await page
    .getByLabel("Upload Resume")
    .setInputFiles(RESUME_FIXTURE);

  await expect(
    page.getByLabel("Use Resume"),
  ).toBeVisible({ timeout: 15000 });

  await page
    .getByRole("button", { name: "Preview Match Score" })
    .click();

  await expect(
    page.getByText("Overall Match Score"),
  ).toBeVisible({ timeout: 30000 });

  await expect(
    page.getByText("Match Breakdown"),
  ).toBeVisible();

  // ---------------------------------------------------------
  // CANDIDATE: apply
  // ---------------------------------------------------------

  await page
    .getByRole("button", { name: "Apply Now" })
    .click();

  await page.waitForURL(/\/candidate\/applications\/\d+/);

  await expect(
    page.getByRole("heading", { name: jobTitle }),
  ).toBeVisible();

  // ---------------------------------------------------------
  // RECRUITER: see the application, open the candidate, shortlist
  // ---------------------------------------------------------

  await page.goto("/login");
  await page.getByLabel("Email").fill(recruiterEmail);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL("**/jobs");

  await page.goto("/recruiter/jobs");
  await page
    .getByRole("link", { name: jobTitle })
    .click();

  await expect(
    page.getByText("1 candidate(s) ranked"),
  ).toBeVisible({ timeout: 15000 });

  await page
    .getByRole("link", { name: candidateName })
    .click();

  await expect(
    page.getByRole("heading", { name: candidateName }),
  ).toBeVisible();
  await expect(
    page.getByText("Overall Match Score"),
  ).toBeVisible();
  await expect(
    page.getByText("Evidence & Citations"),
  ).toBeVisible();

  await page
    .getByRole("button", { name: "Shortlist" })
    .click();

  await expect(
    page.getByText("shortlisted"),
  ).toBeVisible({ timeout: 10000 });

  // ---------------------------------------------------------
  // CANDIDATE: see the updated status and feedback
  // ---------------------------------------------------------

  await page.goto("/login");
  await page.getByLabel("Email").fill(candidateEmail);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL("**/candidate/dashboard", { timeout: 60000 });

  await page.goto("/candidate/applications");

  await expect(
    page.getByRole("cell", { name: jobTitle }),
  ).toBeVisible({ timeout: 15000 });
  await expect(
    page.getByText("shortlisted"),
  ).toBeVisible();

  await page.getByRole("link", { name: "View" }).click();

  await expect(
    page.getByText("Overall Match Score"),
  ).toBeVisible();
  await expect(
    page.getByText("Match Breakdown"),
  ).toBeVisible();
});

test("a candidate is redirected away from recruiter-only routes", async ({
  page,
}) => {
  const ts = Date.now();
  const email = `journey-guard-${ts}@example.com`;
  const password = "StrongPassword123!";

  await page.goto("/register");
  await page.getByRole("radio", { name: "Candidate" }).click();
  await page.getByLabel("Email").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page
    .getByRole("button", { name: "Create Account" })
    .click();

  await page.waitForURL("**/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL("**/candidate/dashboard", { timeout: 60000 });

  // Attempting to visit a recruiter-only route redirects the
  // candidate back into their own portal rather than rendering
  // recruiter UI. The backend independently enforces this on every
  // API call regardless of what the frontend renders.
  await page.goto("/recruiter/jobs");
  await page.waitForURL("**/candidate/dashboard", { timeout: 60000 });
});

test("a candidate cannot apply to a job the recruiter has closed", async ({
  page,
}) => {
  const ts = Date.now();
  const recruiterEmail = `journey-close-recruiter-${ts}@example.com`;
  const candidateEmail = `journey-close-candidate-${ts}@example.com`;
  const password = "StrongPassword123!";
  const jobTitle = `Backend Engineer ${ts}`;

  await page.goto("/register");
  await page.getByRole("radio", { name: "Recruiter" }).click();
  await page.getByLabel("Email").fill(recruiterEmail);
  await page
    .getByLabel("Password", { exact: true })
    .fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page
    .getByRole("button", { name: "Create Account" })
    .click();
  await page.waitForURL("**/login");
  await page.getByLabel("Email").fill(recruiterEmail);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL("**/jobs");

  await page.goto("/recruiter/jobs");
  await page.getByLabel("Job Title").fill(jobTitle);
  await page
    .locator("#recruiter-job-raw-text")
    .fill("Backend Engineer role, closes immediately.");
  await page
    .getByRole("button", { name: "Create Job" })
    .click();
  await expect(
    page.getByRole("link", { name: jobTitle }),
  ).toBeVisible({ timeout: 15000 });

  // Close it right away.
  await page
    .locator("li", { hasText: jobTitle })
    .getByRole("button", { name: "Close" })
    .click();
  await expect(
    page.locator("li", { hasText: jobTitle }),
  ).toContainText("Closed");

  await page.goto("/register");
  await page.getByRole("radio", { name: "Candidate" }).click();
  await page.getByLabel("Email").fill(candidateEmail);
  await page
    .getByLabel("Password", { exact: true })
    .fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page
    .getByRole("button", { name: "Create Account" })
    .click();
  await page.waitForURL("**/login");
  await page.getByLabel("Email").fill(candidateEmail);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL("**/candidate/dashboard", { timeout: 60000 });

  // A closed job never appears in the candidate's open-jobs list.
  await page.goto("/candidate/jobs");
  await page.getByLabel("Search jobs").fill(jobTitle);
  await expect(
    page.getByText("No jobs available"),
  ).toBeVisible();
});
