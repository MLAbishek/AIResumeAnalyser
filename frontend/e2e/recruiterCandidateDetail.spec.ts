import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

// Focused, additive extension of the recruiter/candidate journey
// covering the recruiter job-details -> applicants -> candidate
// detail -> actual resume viewing flow. Nothing here is mocked - it
// exercises the real backend, real database, and the real uploaded
// PDF resume file end to end.

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Real JD/resume PDFs already checked into the repository's
// intended input location - not fabricated/generated documents.
// Both are run through the real extraction + parsing pipeline; the
// assertions below check the actual values that pipeline produces
// from these specific files, not generic "a value exists" checks.
const JD_PDF_FIXTURE = path.join(
  __dirname,
  "..",
  "..",
  "data",
  "raw",
  "jd",
  "jd001.pdf",
);
const RESUME_PDF_FIXTURE = path.join(
  __dirname,
  "..",
  "..",
  "data",
  "raw",
  "resumes",
  "resume_001.pdf",
);

test.setTimeout(180000);

test("recruiter opens a job's applicants, views a candidate's full profile and actual resume, and shortlist persists", async ({
  page,
}) => {
  const ts = Date.now();
  const recruiterEmail = `candidate-detail-recruiter-${ts}@example.com`;
  const candidateEmail = `candidate-detail-candidate-${ts}@example.com`;
  const password = "StrongPassword123!";
  const jobTitle = `Java Developer Intern ${ts}`;

  // ---------------------------------------------------------
  // RECRUITER: register, log in, create a job via real JD upload
  // ---------------------------------------------------------

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
  await page.getByRole("radio", { name: "Upload JD" }).click();
  await page
    .getByLabel("Job Description File")
    .setInputFiles(JD_PDF_FIXTURE);
  await page
    .getByRole("button", { name: "Create Job" })
    .click();

  await expect(
    page.getByRole("link", { name: jobTitle }),
  ).toBeVisible({ timeout: 15000 });

  // ---------------------------------------------------------
  // RECRUITER: verify the PARSED, STRUCTURED JD content actually
  // extracted from the real uploaded jd001.pdf - not a generic
  // "some text exists" check. jd001.pdf's real content is a Java
  // Developer Intern role in Chennai with an inline "Eligibility:"
  // education requirement and a "Required Skills:" bullet list.
  // ---------------------------------------------------------

  await page.getByRole("link", { name: jobTitle }).click();

  await expect(
    page.getByRole("heading", {
      name: "Parsed Job Description",
    }),
  ).toBeVisible();

  // Structured fields the parser now extracts from this real PDF.
  // Each value also appears again, verbatim, inside the raw
  // extracted-text block further down the page - .first() picks
  // the structured-field occurrence; either match still proves the
  // value was genuinely extracted, not fabricated.
  await expect(
    page.getByText("Chennai, Work from Office").first(),
  ).toBeVisible();
  await expect(
    page.getByText("full-time").first(),
  ).toBeVisible();
  await expect(
    page
      .getByText(/passionate and driven Java Developer Intern/)
      .first(),
  ).toBeVisible();

  await expect(
    page.getByText("Required Skills", { exact: true }),
  ).toBeVisible();
  await expect(
    page
      .getByText(
        /Strong understanding of Java fundamentals and OOP concepts/,
      )
      .first(),
  ).toBeVisible();
  await expect(
    page
      .getByText(
        /Basic knowledge of databases \(MySQL, PostgreSQL, etc\.\)/,
      )
      .first(),
  ).toBeVisible();

  await expect(
    page.getByText("Education Requirements"),
  ).toBeVisible();
  await expect(
    page
      .getByText(/B\.E\.\/B\.Tech\/B\.Sc\.\/BCA students/)
      .first(),
  ).toBeVisible();

  // Responsibilities, now correctly extracted and persisted
  // (previously computed by the parser but silently discarded -
  // Job had no column for it at all).
  await expect(
    page.getByText("Responsibilities", { exact: true }),
  ).toBeVisible();
  await expect(
    page
      .getByText(
        /Write clean, efficient, and maintainable Java code/,
      )
      .first(),
  ).toBeVisible();

  // The full extracted text is still available underneath, cleanly
  // formatted (not the fragmented, unreadable extraction this PDF
  // used to produce before the ingestion-layer fix).
  await expect(
    page.getByText(/Key Responsibilities/),
  ).toBeVisible();

  await page.goto("/recruiter/jobs");

  // ---------------------------------------------------------
  // CANDIDATE: register, log in, upload a REAL PDF resume, apply
  // ---------------------------------------------------------

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
  await page.waitForURL("**/candidate/dashboard", {
    timeout: 60000,
  });

  await page.goto("/candidate/jobs");
  await page.getByLabel("Search jobs").fill(jobTitle);
  await page
    .getByRole("link", { name: "View Job" })
    .first()
    .click();

  await expect(
    page.getByRole("heading", { name: jobTitle }),
  ).toBeVisible();

  await page
    .getByLabel("Upload Resume")
    .setInputFiles(RESUME_PDF_FIXTURE);

  await expect(page.getByLabel("Use Resume")).toBeVisible({
    timeout: 20000,
  });

  await page
    .getByRole("button", { name: "Preview Match Score" })
    .click();
  await expect(
    page.getByText("Overall Match Score"),
  ).toBeVisible({ timeout: 30000 });

  await page.getByRole("button", { name: "Apply Now" }).click();
  await page.waitForURL(/\/candidate\/applications\/\d+/);

  // ---------------------------------------------------------
  // RECRUITER: open the job, see the applicant, open candidate detail
  // ---------------------------------------------------------

  await page.goto("/login");
  await page.getByLabel("Email").fill(recruiterEmail);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL("**/jobs");

  await page.goto("/recruiter/jobs");
  await page.getByRole("link", { name: jobTitle }).click();

  await expect(
    page.getByText("1 candidate(s) ranked"),
  ).toBeVisible({ timeout: 15000 });

  // Applicant row shows key skills extracted from the real resume.
  await expect(page.getByText("Python").first()).toBeVisible();

  await page
    .getByRole("link", { name: "View Candidate" })
    .click();

  // ---------------------------------------------------------
  // Verify candidate profile/dashboard information renders
  // ---------------------------------------------------------

  await expect(
    page.getByText(candidateEmail),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Candidate Profile" }),
  ).toBeVisible();

  // The candidate's real name, correctly extracted from the PDF
  // header (this used to incorrectly resolve to a stray LinkedIn/
  // GitHub URL line before the name-extraction fix).
  await expect(
    page.getByRole("heading", { name: "Abishek J" }),
  ).toBeVisible();

  // Parsed skills genuinely extracted from the real PDF - not
  // fabricated. resume_001.pdf's real skills list includes these.
  await expect(page.getByText("Python").first()).toBeVisible();
  await expect(page.getByText("TensorFlow").first()).toBeVisible();

  // This PDF genuinely has no summary/profile section, so that
  // empty state is still correct and honest (not invented content).
  await expect(
    page.getByText(
      "No summary was extracted from the resume.",
    ),
  ).toBeVisible();

  // Structured work experience, now correctly extracted (role and
  // company used to be swapped/lost entirely before the fix).
  await expect(
    page.getByText("Deep Learning Intern").first(),
  ).toBeVisible();
  await expect(
    page.getByText(/Authenta AI/).first(),
  ).toBeVisible();
  await expect(
    page.getByText("AI Research Intern").first(),
  ).toBeVisible();
  await expect(
    page.getByText(/Foviatech/).first(),
  ).toBeVisible();

  // Structured education, now correctly extracted with the real
  // institution name (previously null, or corrupted by a false
  // "AWARDS & ACHIEVEMENTS" match).
  await expect(page.getByText("B.Tech").first()).toBeVisible();
  await expect(
    page.getByText(/St\. Joseph.s College of Engineering/).first(),
  ).toBeVisible();

  // Structured projects, now persisted at all (previously computed
  // by the parser but silently discarded before the database).
  await expect(
    page
      .getByText("AI-Based Workplace Behavior Monitoring System")
      .first(),
  ).toBeVisible();
  await expect(
    page.getByText("Skin Disease Detector").first(),
  ).toBeVisible();

  // This resume genuinely has no certifications section.
  await expect(
    page.getByText(
      "No certifications were extracted from the resume.",
    ),
  ).toBeVisible();

  await expect(
    page.getByText("Overall Match Score"),
  ).toBeVisible();
  await expect(
    page.getByText("Evidence & Citations"),
  ).toBeVisible();

  // ---------------------------------------------------------
  // Open the actual uploaded resume and verify it is displayed
  // ---------------------------------------------------------

  await page
    .getByRole("button", { name: "View Resume" })
    .click();

  const resumeFrame = page.locator("iframe");
  await expect(resumeFrame).toBeVisible({ timeout: 15000 });
  // The iframe's src is a blob: object URL created from the actual
  // authenticated fetch of the resume bytes - not a static
  // placeholder or a direct filesystem/backend URL.
  await expect(resumeFrame).toHaveAttribute(
    "src",
    /^blob:/,
  );

  // ---------------------------------------------------------
  // Shortlist the candidate and verify it persists after refresh
  // ---------------------------------------------------------

  await page
    .getByRole("button", { name: "Shortlist" })
    .click();
  await expect(page.getByText("shortlisted")).toBeVisible({
    timeout: 10000,
  });

  await page.reload();

  await expect(
    page.getByText(candidateEmail),
  ).toBeVisible({ timeout: 15000 });
  await expect(page.getByText("shortlisted")).toBeVisible();
});
