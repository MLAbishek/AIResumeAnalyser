/**
 * Minimal ambient types for the Google Identity Services browser
 * library (loaded at runtime from https://accounts.google.com/gsi/client -
 * see src/lib/googleIdentity.ts). Only the surface this app actually
 * uses is declared.
 */

interface GoogleCredentialResponse {
  credential: string;
  select_by?: string;
}

interface GoogleIdConfiguration {
  client_id: string;
  callback: (response: GoogleCredentialResponse) => void;
  auto_select?: boolean;
  ux_mode?: "popup" | "redirect";
}

interface GoogleButtonConfiguration {
  type?: "standard" | "icon";
  theme?: "outline" | "filled_blue" | "filled_black";
  size?: "large" | "medium" | "small";
  text?: "signin_with" | "signup_with" | "continue_with" | "signin";
  shape?: "rectangular" | "pill" | "circle" | "square";
  width?: number | string;
  logo_alignment?: "left" | "center";
}

interface GoogleAccountsId {
  initialize: (config: GoogleIdConfiguration) => void;
  renderButton: (
    parent: HTMLElement,
    options: GoogleButtonConfiguration,
  ) => void;
  prompt: () => void;
  cancel: () => void;
  disableAutoSelect: () => void;
}

interface Window {
  google?: {
    accounts: {
      id: GoogleAccountsId;
    };
  };
}
