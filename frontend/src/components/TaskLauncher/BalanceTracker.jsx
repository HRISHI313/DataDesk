import "./BalanceTracker.css";

/**
 * Shows each analyst's current assigned count against their target,
 * color-coded:
 *   blue   - still filling up (well under target)
 *   yellow - getting close to target
 *   green  - on target
 *   red    - over target
 *
 * All of this is computed from data already in the browser - no backend
 * call happens when this re-renders, which is the whole point of moving
 * off Streamlit for this screen.
 */
function statusFor(assigned, target) {
  if (target <= 0) return "neutral";
  if (assigned > target) return "over";
  if (assigned === target) return "onTarget";
  if (assigned >= target * 0.85) return "near";
  return "filling";
}

const STATUS_LABEL = {
  filling: "Filling",
  near: "Near target",
  onTarget: "On target",
  over: "Over target",
  neutral: "—",
};

export default function BalanceTracker({ analysts, assignedCounts, target }) {
  return (
    <div className="balance-tracker">
      {analysts.map((name) => {
        const assigned = assignedCounts[name] || 0;
        const status = statusFor(assigned, target);
        const pct = target > 0 ? Math.min((assigned / target) * 100, 100) : 0;

        return (
          <div className="balance-row" key={name}>
            <div className="balance-row-header">
              <span className="balance-name">{name}</span>
              <span className={`balance-count status-${status}`}>
                {assigned} / {target || "—"}
              </span>
            </div>
            <div className="balance-bar-track">
              <div
                className={`balance-bar-fill status-${status}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className={`balance-status-label status-${status}`}>
              {STATUS_LABEL[status]}
            </span>
          </div>
        );
      })}
    </div>
  );
}
