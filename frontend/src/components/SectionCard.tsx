import type { ReactNode } from "react";

type SectionCardProps = {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
};

export default function SectionCard({
  title,
  subtitle,
  actions,
  children,
  className,
}: SectionCardProps) {
  return (
    <section className={`card${className ? ` ${className}` : ""}`}>
      {(title || actions) && (
        <div className="card__head">
          <div>
            {title && <h2>{title}</h2>}
            {subtitle && (
              <p className="card__subtitle">{subtitle}</p>
            )}
          </div>
          {actions && (
            <div className="card__actions">{actions}</div>
          )}
        </div>
      )}
      {!title && subtitle && (
        <p className="card__subtitle">{subtitle}</p>
      )}
      {children}
    </section>
  );
}
