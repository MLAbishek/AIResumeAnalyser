import type { ReactNode } from "react";
import { IconAlertTriangle, IconInbox } from "./icons";

type StateProps = {
  title?: string;
  message: string;
};

type EmptyStateProps = StateProps & {
  action?: ReactNode;
};

type ErrorStateProps = StateProps & {
  onRetry?: () => void;
  retryLabel?: string;
};

export function LoadingState({
  message,
}: StateProps) {
  return (
    <section
      role="status"
      aria-live="polite"
      className="state-panel"
    >
      <span className="spinner" aria-hidden="true" />
      <p>{message}</p>
    </section>
  );
}

export function EmptyState({
  title = "No data available",
  message,
  action,
}: EmptyStateProps) {
  return (
    <section role="status" className="state-panel">
      <IconInbox className="state-panel__icon" />
      <h2>{title}</h2>
      <p>{message}</p>
      {action && (
        <div className="state-panel__action">{action}</div>
      )}
    </section>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  retryLabel = "Retry",
}: ErrorStateProps) {
  return (
    <section role="alert" className="state-panel state-panel--error">
      <IconAlertTriangle className="state-panel__icon" />
      <h2>{title}</h2>
      <p>{message}</p>

      {onRetry && (
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onRetry}
        >
          {retryLabel}
        </button>
      )}
    </section>
  );
}

export function ValidationMessage({
  message,
}: {
  message: string;
}) {
  return (
    <p role="alert" className="validation-message">
      <IconAlertTriangle
        width={14}
        height={14}
        strokeWidth={2.2}
      />
      {message}
    </p>
  );
}
