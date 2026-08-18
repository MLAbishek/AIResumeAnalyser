import type { ReactNode } from "react";

type StatCardProps = {
  icon?: ReactNode;
  label: string;
  value: ReactNode;
  hint?: string;
};

export default function StatCard({
  icon,
  label,
  value,
  hint,
}: StatCardProps) {
  return (
    <div className="stat-card">
      {icon && <div className="stat-card__icon">{icon}</div>}
      <div className="stat-card__body">
        <p className="stat-card__label">{label}</p>
        <p className="stat-card__value">{value}</p>
        {hint && <p className="stat-card__hint">{hint}</p>}
      </div>
    </div>
  );
}
