import "./PctBreakdown.css";

/** data shape: { "Label": {count, pct}, ... } */
export default function PctBreakdown({ data }) {
  const entries = Object.entries(data || {});
  return (
    <div className="pct-breakdown">
      {entries.map(([label, { count, pct }]) => (
        <div className="pct-row" key={label}>
          <div className="pct-row-header">
            <span>{label}</span>
            <span>
              {count} ({pct}%)
            </span>
          </div>
          <div className="pct-bar-track">
            <div className="pct-bar-fill" style={{ width: `${Math.min(pct, 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
