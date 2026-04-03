export default function SummaryCard({ label, value, hint, accent = "leaf" }) {
  return (
    <article className={`summary-card accent-${accent}`}>
      <span className="summary-label">{label}</span>
      <strong className="summary-value">{value}</strong>
      <span className="summary-hint">{hint}</span>
    </article>
  );
}
