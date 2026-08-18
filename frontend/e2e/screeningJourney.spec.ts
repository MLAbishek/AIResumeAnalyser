import { expect, Page, test } from "@playwright/test";

// These tests drive the real Vite dev server against the real local backend
// (see playwright.config.ts). The backend must already be running:
//   uvicorn main:app --reload
// The test user below is the same account used by the Vitest integration
// test (src/integration/screeningWorkflow.test.ts) and is expected to
// already exist in the local database.

const TEST_EMAIL = "frontend-test@example.com";
const TEST_PASSWORD = "FrontendTest123!";

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(TEST_EMAIL);
  await page.getByLabel("Password").fill(TEST_PASSWORD);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL("**/jobs");
}

test.describe("Recruiter workflow (happy path)", () => {
  test("completes login -> job -> resume -> screening -> ranking -> profile -> history", async ({
    page,
  }) => {
    const suffix = Date.now();
    const jobTitle = `E2E Frontend Engineer ${suffix}`;
    const resumeId = `e2e-resume-${suffix}`;
    const candidateName = `E2E Candidate ${suffix}`;

    await login(page);

    // ---- Jobs (F04) ----
    await page.goto("/jobs");

    await page.getByLabel("Job Title").fill(jobTitle);
    await page
      .getByLabel("Raw Job Description")
      .fill(
        "Frontend Engineer with React and TypeScript experience.",
      );

    await page
      .getByRole("button", { name: "Create Job" })
      .click();

    await expect(
      page.getByText(jobTitle),
    ).toBeVisible();

    // ---- Resumes (F05) ----
    await page.goto("/resumes");

    await page.getByLabel("Resume ID").fill(resumeId);
    await page.getByLabel("Name").fill(candidateName);
    await page
      .getByLabel("Skills")
      .fill("React, TypeScript");
    await page
      .getByLabel("Total Experience (months)")
      .fill("24");

    await page
      .getByRole("button", { name: "Create Resume" })
      .click();

    await expect(
      page.getByText(resumeId),
    ).toBeVisible();

    // ---- Screening (F07) ----
    await page.goto("/screening");

    await page
      .getByLabel("Job Description")
      .selectOption({ label: jobTitle });

    await page
      .locator("li")
      .filter({ hasText: candidateName })
      .getByRole("checkbox")
      .check();

    await page
      .getByRole("button", { name: "Start Screening" })
      .click();

    await expect(
      page.getByRole("heading", {
        name: "Screening Completed",
      }),
    ).toBeVisible({ timeout: 30000 });

    // ---- Ranking (F08) ----
    await page.goto("/ranking");

    const rankingJobSelect = page.getByLabel(
      "Job Description",
    );
    await rankingJobSelect.selectOption({
      label: jobTitle,
    });

    const rankedJobId = await rankingJobSelect.inputValue();

    await page
      .getByRole("button", { name: "Load Ranking" })
      .click();

    await expect(
      page.getByText(resumeId),
    ).toBeVisible({ timeout: 15000 });

    await page
      .getByRole("link", { name: candidateName })
      .click();

    // ---- Candidate Match Profile / Explainability (F09/F10) ----
    await expect(
      page.getByRole("heading", {
        name: "Candidate Match Profile",
      }),
    ).toBeVisible();

    await expect(
      page.getByText(resumeId),
    ).toBeVisible();

    await expect(
      page.getByText("Evidence & Citations"),
    ).toBeVisible();

    // Back-link should preserve job context via the query string.
    await page
      .getByRole("link", { name: "← Back to Ranking" })
      .click();

    await page.waitForURL(/\/ranking\?jobId=/);

    await expect(
      page.getByLabel("Job Description"),
    ).toHaveValue(rankedJobId);

    // ---- Screening History (F11) ----
    await page.goto("/screening-history");

    await page
      .getByLabel("Job Description")
      .selectOption({ label: jobTitle });

    await page
      .getByRole("button", {
        name: "Load Screening History",
      })
      .click();

    await expect(
      page.getByText(resumeId),
    ).toBeVisible({ timeout: 15000 });
  });
});

test.describe("Failure paths", () => {
  test("shows an error for invalid login credentials", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(TEST_EMAIL);
    await page
      .getByLabel("Password")
      .fill("WrongPassword123!");

    await page
      .getByRole("button", { name: "Login" })
      .click();

    await expect(
      page.getByText("Invalid email or password."),
    ).toBeVisible();

    await expect(page).toHaveURL(/\/login$/);
  });

  test("blocks unauthenticated access to protected pages", async ({
    page,
  }) => {
    await page.goto("/jobs");

    await expect(
      page.getByRole("heading", {
        name: "Job Management",
      }),
    ).toBeVisible();

    await expect(
      page.getByText("Authentication required."),
    ).toBeVisible();
  });

  test("redirects unknown routes to the 404 page", async ({
    page,
  }) => {
    await page.goto("/this-route-does-not-exist");

    await expect(
      page.getByRole("heading", { name: "404" }),
    ).toBeVisible();

    await expect(
      page.getByText("Page not found."),
    ).toBeVisible();
  });

  test("disables screening submission until a job and resume are selected", async ({
    page,
  }) => {
    await login(page);
    await page.goto("/screening");

    await expect(
      page.getByRole("button", {
        name: "Start Screening",
      }),
    ).toBeDisabled();
  });

  test("shows a recoverable error state when the candidate profile API call fails", async ({
    page,
  }) => {
    await login(page);

    await page.goto(
      "/ranking/e2e-nonexistent-job/e2e-nonexistent-resume",
    );

    await expect(
      page.getByRole("alert"),
    ).toBeVisible();

    await page
      .getByRole("button", { name: "Retry" })
      .click();

    // Retry reloads the page; the same invalid IDs still error out,
    // so the app should show the error state again, not crash.
    await expect(
      page.getByRole("heading", {
        name: "Candidate Match Profile",
      }),
    ).toBeVisible();

    await expect(
      page.getByRole("alert"),
    ).toBeVisible();
  });
});
