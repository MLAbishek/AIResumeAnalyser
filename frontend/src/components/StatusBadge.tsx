import type { ReactNode } from "react";
import { IconAlertTriangle, IconCheck, IconX } from "./icons";

export function EligibilityBadge({
  eligible,
}: {
  eligible: boolean;
}) {
  if (eligible) {
    return (
      <span className="badge badge-success">
        <IconCheck width={12} height={12} strokeWidth={2.4} />
        Eligible
      </span>
    );
  }

  return (
    <span className="badge badge-danger">
      <IconX width={12} height={12} strokeWidth={2.4} />
      Not Eligible
    </span>
  );
}

type DecisionTone = "success" | "warning" | "danger" | "neutral";

function toneForDecision(
  decision: string | null | undefined,
): DecisionTone {
  const normalized = decision?.toLowerCase().trim();

  if (
    normalized === "shortlist" ||
    normalized === "shortlisted" ||
    normalized === "accept" ||
    normalized === "accepted"
  ) {
    return "success";
  }

  if (
    normalized === "review" ||
    normalized === "hold" ||
    normalized === "maybe"
  ) {
    return "warning";
  }

  if (
    normalized === "reject" ||
    normalized === "rejected"
  ) {
    return "danger";
  }

  return "neutral";
}

export function DecisionBadge({
  decision,
}: {
  decision: string | null | undefined;
}) {
  const tone = toneForDecision(decision);

  return (
    <span className={`badge badge-${tone}`}>
      {decision ?? "—"}
    </span>
  );
}

export function WarningBadge({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <span className="badge badge-warning">
      <IconAlertTriangle
        width={12}
        height={12}
        strokeWidth={2.2}
      />
      {children}
    </span>
  );
}
