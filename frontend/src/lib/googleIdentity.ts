const SCRIPT_SRC = "https://accounts.google.com/gsi/client";

export const GOOGLE_CLIENT_ID: string =
  import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

export function isGoogleSignInConfigured(): boolean {
  return GOOGLE_CLIENT_ID.trim().length > 0;
}

let loadPromise: Promise<void> | null = null;

/**
 * Load the official Google Identity Services script once and reuse
 * it for every mount - this is the library Google's own guidance
 * requires for rendering the real "Sign in with Google" button
 * rather than a look-alike:
 * https://developers.google.com/identity/gsi/web/guides/display-button
 */
export function loadGoogleIdentityScript(): Promise<void> {
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }

  if (loadPromise) {
    return loadPromise;
  }

  loadPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector(
      `script[src="${SCRIPT_SRC}"]`,
    );

    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () =>
        reject(
          new Error(
            "Failed to load Google Identity Services.",
          ),
        ),
      );
      return;
    }

    const script = document.createElement("script");
    script.src = SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () =>
      reject(
        new Error(
          "Failed to load Google Identity Services.",
        ),
      );

    document.head.appendChild(script);
  });

  return loadPromise;
}
