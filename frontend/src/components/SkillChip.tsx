type SkillChipProps = {
  children: string;
  tone?: "neutral" | "success" | "danger";
};

export default function SkillChip({
  children,
  tone = "neutral",
}: SkillChipProps) {
  return (
    <span className={`chip chip-${tone}`}>{children}</span>
  );
}
