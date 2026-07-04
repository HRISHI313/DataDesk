import "./SummaryCards.css";

export default function SummaryCards({ results }) {
  const { total_records, unique_retailers_count, polygon_pct, polygon_coverage } = results;

  const verifiedPct = polygon_pct?.["Verified QA"]?.pct ?? 0;
  const markedPct = polygon_coverage?.marked_pct ?? 0;
  const pendingPct = polygon_coverage?.pending_pct ?? 0;

  return (
    <div className="summary-cards">
      <div className="summary-card">
        <span className="summary-value">{total_records}</span>
        <span className="summary-label">Total records</span>
      </div>
      <div className="summary-card">
        <span className="summary-value">{unique_retailers_count}</span>
        <span className="summary-label">Retailers</span>
      </div>
      <div className="summary-card">
        <span className="summary-value">{verifiedPct}%</span>
        <span className="summary-label">Verified QA</span>
      </div>
      <div className="summary-card">
        <span className="summary-value tone-good">{markedPct}%</span>
        <span className="summary-label">Marked</span>
      </div>
      <div className="summary-card">
        <span className="summary-value tone-warn">{pendingPct}%</span>
        <span className="summary-label">Pending</span>
      </div>
    </div>
  );
}
