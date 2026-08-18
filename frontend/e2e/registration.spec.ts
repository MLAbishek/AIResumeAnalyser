import { expect, test } from "@playwright/test";

// This test creates a brand-new account through the real registration
// endpoint on every run (unique email via Date.now()) and never touches
// the shared frontend-test@example.com account used by the other E2E
// and integration tests.

test.describe("Registration", () => {
  test("registers a new account, then logs in and reaches Jobs", async ({
    page,
  }) => {
    const email = `registration-${Date.now()}@example.com`;
    const password = "StrongPassword123!";

    await page.goto("/register");

    await page.getByLabel("Email").fill(email);
    await page
      .getByLabel("Password", { exact: true })
      .fill(password);
    await page
      .getByLabel("Confirm Password")
      .fill(password);

    await page
      .getByRole("button", { name: "Create Account" })
      .click();

    // Successful registration redirects to /login with a success banner.
    await page.waitForURL("**/login");

    await expect(
      page.getByText("Account created"),
    ).toBeVisible();

    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page
      .getByRole("button", { name: "Login" })
      .click();

    await page.waitForURL("**/jobs");

    await expect(
      page.getByRole("heading", {
        name: "Job Management",
      }),
    ).toBeVisible();

    // Authenticated navigation should now be visible.
    await expect(
      page.getByRole("link", { name: "Jobs" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Logout" }),
    ).toBeVisible();
  });

  test("shows a clean error when registering with an email that already exists", async ({
    page,
  }) => {
    const email = `registration-dup-${Date.now()}@example.com`;
    const password = "StrongPassword123!";

    await page.goto("/register");
    await page.getByLabel("Email").fill(email);
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

    // Register the same email again.
    await page.goto("/register");
    await page.getByLabel("Email").fill(email);
    await page
      .getByLabel("Password", { exact: true })
      .fill(password);
    await page
      .getByLabel("Confirm Password")
      .fill(password);
    await page
      .getByRole("button", { name: "Create Account" })
      .click();

    await expect(
      page.getByText(
        "An account with this email already exists.",
      ),
    ).toBeVisible();

    // Must not have navigated away on failure.
    await expect(page).toHaveURL(/\/register$/);
  });

  test("rejects mismatched passwords on the registration form", async ({
    page,
  }) => {
    await page.goto("/register");

    await page
      .getByLabel("Email")
      .fill(`registration-mismatch-${Date.now()}@example.com`);
    await page
      .getByLabel("Password", { exact: true })
      .fill("StrongPassword123!");
    await page
      .getByLabel("Confirm Password")
      .fill("DifferentPassword123!");

    await page
      .getByRole("button", { name: "Create Account" })
      .click();

    await expect(
      page.getByText("Passwords do not match."),
    ).toBeVisible();

    await expect(page).toHaveURL(/\/register$/);
  });
});
