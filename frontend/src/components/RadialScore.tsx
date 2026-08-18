const SIZE = 120;
const STROKE = 10;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function scoreTone(value: number): "high" | "mid" | "low" {
  if (value >= 75) return "high";
  if (value >= 50) return "mid";
  return "low";
}

function scoreLabel(value: number): string {
  if (value >= 85) return "Excellent Match";
  if (value >= 70) return "Strong Match";
  if (value >= 50) return "Moderate Match";
  return "Weak Match";
}

/**
 * Circular progress visualization for an overall AI match score.
 * Never fabricates a value - `value` must come directly from a
 * persisted backend screening result.
 */
export default function RadialScore({
  value,
  label,
}: {
  value: number;
  label?: string;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  const tone = scoreTone(clamped);
  const offset =
    CIRCUMFERENCE - (clamped / 100) * CIRCUMFERENCE;

  return (
    <div className="radial-score">
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        role="img"
        aria-label={`Overall match score ${clamped.toFixed(1)} percent`}
      >
        <circle
          className="radial-score__track"
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          strokeWidth={STROKE}
          fill="none"
        />
        <circle
          className={`radial-score__fill radial-score__fill--${tone}`}
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          strokeWidth={STROKE}
          fill="none"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
        />
        <text
          x="50%"
          y="47%"
          textAnchor="middle"
          dominantBaseline="middle"
          className="radial-score__value"
        >
          {clamped.toFixed(1)}%
        </text>
        <text
          x="50%"
          y="66%"
          textAnchor="middle"
          dominantBaseline="middle"
          className="radial-score__caption"
        >
          {label ?? scoreLabel(clamped)}
        </text>
      </svg>
    </div>
  );
}
