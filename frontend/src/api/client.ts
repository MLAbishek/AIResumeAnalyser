import { API_BASE_URL } from "./config";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super(`API request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export function getApiErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  if (error instanceof ApiError) {
    if (
      typeof error.data === "object" &&
      error.data !== null &&
      "detail" in error.data
    ) {
      const detail = (
        error.data as {
          detail?: unknown;
        }
      ).detail;

      if (typeof detail === "string") {
        return detail;
      }
    }

    if (typeof error.data === "string") {
      return error.data;
    }

    if (error.status === 401) {
      return "Your session has expired. Please sign in again.";
    }

    if (error.status === 403) {
      return "You do not have permission to perform this action.";
    }

    if (error.status === 404) {
      return "The requested resource was not found.";
    }

    if (error.status >= 500) {
      return "The server could not complete the request. Please try again.";
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}

type RequestOptions = RequestInit & {
  token?: string;
};

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { token, headers, ...requestOptions } = options;

  // A FormData body (file uploads) must let the browser set its own
  // multipart Content-Type with the correct boundary - forcing
  // application/json here would break the upload.
  const isFormData =
    typeof FormData !== "undefined" &&
    requestOptions.body instanceof FormData;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...requestOptions,
    headers: {
      ...(isFormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...headers,
      ...(token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {}),
    },
  });

  const contentType = response.headers.get("content-type");

  const data = contentType?.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw new ApiError(response.status, data);
  }

  return data as T;
}