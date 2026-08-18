type ScoreBarProps = {
  value: number;
  label?: string;
};

function bandForScore(percent: number): string {
  if (percent >= 75) return "high";
  if (percent >= 50) return "mid";
  return "low";
}

export default function ScoreBar({
  value,
  label,
}: ScoreBarProps) {
  const percent = Math.max(
    0,
    Math.min(100, value),
  );

  const band = bandForScore(percent);

  return (
    <div className="score-bar">
      <div
        className="score-bar__track"
        role="progressbar"
        aria-valuenow={Math.round(percent)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ?? "Score"}
      >
        <div
          className={`score-bar__fill score-bar__fill--${band}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="score-bar__value">
        {percent.toFixed(1)}%
      </span>
    </div>
  );
}
