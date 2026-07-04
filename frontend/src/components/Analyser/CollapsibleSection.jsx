import { useState } from "react";
import "./CollapsibleSection.css";

export default function CollapsibleSection({ title, badge, badgeTone = "neutral", defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="collapsible-section">
      <button className="collapsible-header" onClick={() => setOpen((o) => !o)}>
        <span className="collapsible-chevron">{open ? "▾" : "▸"}</span>
        <span className="collapsible-title">{title}</span>
        {badge !== undefined && (
          <span className={`collapsible-badge tone-${badgeTone}`}>{badge}</span>
        )}
      </button>
      {open && <div className="collapsible-body">{children}</div>}
    </div>
  );
}
