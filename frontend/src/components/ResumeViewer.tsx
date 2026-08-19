import { useEffect, useRef, useState } from "react";
import { getApplicationResumeBlob } from "../api";
import { getApiErrorMessage } from "../api/client";
import { IconDownload, IconEye, IconFileText } from "./icons";

type Props = {
  jobId: string;
  applicationId: number;
  resumeId: string;
};

type Status = "idle" | "loading" | "ready" | "error" | "missing";

/**
 * Loads the candidate's actual uploaded resume file on demand (via
 * the authenticated GET .../applications/{id}/resume endpoint) and
 * either embeds it (PDF) or offers a secure download - never a
 * fake/generated document, and never a direct filesystem path.
 */
export default function ResumeViewer({
  jobId,
  applicationId,
  resumeId,
}: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [objectUrl, setObjectUrl] = useState<string | null>(
    null,
  );
  const [mimeType, setMimeType] = useState<string | null>(
    null,
  );
  const [showViewer, setShowViewer] = useState(false);
  const downloadAnchorRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function ensureLoaded(): Promise<string | null> {
    if (objectUrl) {
      return objectUrl;
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Authentication required.");
      setStatus("error");
      return null;
    }

    setStatus("loading");
    setError(null);

    try {
      const blob = await getApplicationResumeBlob(
        jobId,
        applicationId,
        token,
      );
      const url = URL.createObjectURL(blob);
      setObjectUrl(url);
      setMimeType(blob.type);
      setStatus("ready");
      return url;
    } catch (err) {
      console.error("Failed to load resume:", err);

      const isMissing =
        typeof err === "object" &&
        err !== null &&
        "status" in err &&
        (err as { status?: number }).status === 404;

      setStatus(isMissing ? "missing" : "error");
      setError(
        getApiErrorMessage(
          err,
          "Failed to load the resume file.",
        ),
      );
      return null;
    }
  }

  async function handleView() {
    const url = await ensureLoaded();
    if (url) {
      setShowViewer(true);
    }
  }

  async function handleDownload() {
    const url = await ensureLoaded();
    if (url && downloadAnchorRef.current) {
      downloadAnchorRef.current.href = url;
      downloadAnchorRef.current.download = `${resumeId}${
        mimeType === "application/pdf" ? ".pdf" : ""
      }`;
      downloadAnchorRef.current.click();
    }
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        <span className="stat-card__icon">
          <IconFileText width={16} height={16} />
        </span>
        <div style={{ flex: 1, minWidth: "10rem" }}>
          <p style={{ margin: 0, fontWeight: 650 }}>
            {resumeId}
          </p>
          <p className="muted text-sm mt-0">
            Uploaded resume file
          </p>
        </div>
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            flexWrap: "wrap",
          }}
        >
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleView}
            disabled={status === "loading"}
          >
            {status === "loading" ? (
              <span
                className="spinner-inline"
                aria-hidden="true"
              />
            ) : (
              <IconEye width={16} height={16} />
            )}
            View Resume
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleDownload}
            disabled={status === "loading"}
          >
            <IconDownload width={16} height={16} />
            Download Resume
          </button>
          {/* Hidden anchor used purely to trigger a browser save,
              once the file is loaded as an authenticated blob. */}
          <a
            ref={downloadAnchorRef}
            style={{ display: "none" }}
            aria-hidden="true"
          >
            download
          </a>
        </div>
      </div>

      {status === "missing" && (
        <p
          className="muted text-sm"
          style={{ marginTop: "0.75rem" }}
        >
          The original resume file is not available for this
          application.
        </p>
      )}

      {status === "error" && error && (
        <p
          role="alert"
          className="validation-message"
          style={{ marginTop: "0.75rem" }}
        >
          {error}
        </p>
      )}

      {showViewer && objectUrl && (
        <div style={{ marginTop: "1rem" }}>
          {mimeType === "application/pdf" ? (
            <iframe
              src={objectUrl}
              title={`Resume ${resumeId}`}
              style={{
                width: "100%",
                height: "70vh",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
              }}
            />
          ) : (
            <p className="muted text-sm">
              This file type can&apos;t be previewed inline.
              Use Download Resume to open it.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
