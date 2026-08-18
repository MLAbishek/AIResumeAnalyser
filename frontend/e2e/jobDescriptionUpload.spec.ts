import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

// Focused, additive extension of the recruiter/candidate journey: a
// recruiter creates a job by uploading a JD file instead of typing
// one, and the rest of the pipeline (candidate discovery, resume
// upload, AI match preview, apply, recruiter review) behaves
// identically to the typed-JD path covered by
// recruiterCandidateJourney.spec.ts. Nothing here is mocked - it
// exercises the real backend end-to-end.

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const JD_FIXTURE = path.join(
  __dirname,
  "fixtures",
  "sample-job-description.txt",
);
const RESUME_FIXTURE = path.join(
  __dirname,
  "fixtures",
  "sample-resume.txt",
);

test.setTimeout(180000);

test("recruiter creates a job by uploading a JD file, and a candidate discovers and applies to it", async ({
  page,
}) => {
  const ts = Date.now();
  const recruiterEmail = `journey-jdupload-recruiter-${ts}@example.com`;
  const candidateEmail = `journey-jdupload-candidate-${ts}@example.com`;
  const password = "StrongPassword123!";
  const jobTitle = `Backend Engineer ${ts}`;
  const candidateName = "Taylor Morgan";

  // ---------------------------------------------------------
  // RECRUITER: register, log in, create a job via JD upload
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
    .getByRole("radio", { name: "Upload JD" })
    .click();
  await page
    .getByLabel("Job Description File")
    .setInputFiles(JD_FIXTURE);

  await expect(
    page.getByText("Selected: sample-job-description.txt"),
  ).toBeVisible();

  await page
    .getByRole("button", { name: "Create Job" })
    .click();

  await expect(
    page.getByRole("link", { name: jobTitle }),
  ).toBeVisible({ timeout: 15000 });

  // ---------------------------------------------------------
  // CANDIDATE: register, log in, discover the uploaded-JD job
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
  await page.waitForURL("**/candidate/dashboard", {
    timeout: 60000,
  });

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

  // The extracted JD text (from the uploaded .txt file) reached the
  // same job record the candidate-facing detail page reads from.
  await expect(
    page.getByText(/Python/i).first(),
  ).toBeVisible();

  // ---------------------------------------------------------
  // CANDIDATE: upload a resume, get a real AI match score, apply
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

  await page
    .getByRole("button", { name: "Apply Now" })
    .click();

  await page.waitForURL(/\/candidate\/applications\/\d+/);

  await expect(
    page.getByRole("heading", { name: jobTitle }),
  ).toBeVisible();

  // ---------------------------------------------------------
  // RECRUITER: confirm the application shows up against the
  // uploaded-JD job, ranked by the same AI pipeline.
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
});
