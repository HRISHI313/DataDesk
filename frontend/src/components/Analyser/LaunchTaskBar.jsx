import { useState } from "react";
import { launchTaskPreview, launchTask } from "../../api/analyser";
import "./LaunchTaskBar.css";

/**
 * Two-step flow:
 *  1. Click "Launch Task" -> fetch per-retailer "needs work" counts and
 *     expand a checklist in place (no page change yet). Retailers with 0
 *     remaining are shown greyed out and unchecked, not hidden.
 *  2. Adjust selection if needed, click "Confirm" -> filters to selected
 *     retailers and hands off to Task Launcher's assignment screen.
 */
export default function LaunchTaskBar({ uploadId, onLaunchTask }) {
  const [step, setStep] = useState("idle"); // idle | loading-preview | reviewing | launching
  const [retailers, setRetailers] = useState([]); // [{name, needs_work_count}]
  const [selected, setSelected] = useState(new Set());
  const [error, setError] = useState("");

  async function handleOpenChecklist() {
    if (!uploadId) return;
    setStep("loading-preview");
    setError("");
    try {
      const result = await launchTaskPreview(uploadId);
      setRetailers(result.retailers);
      setSelected(new Set(result.retailers.filter((r) => r.needs_work_count > 0).map((r) => r.name)));
      setStep("reviewing");
    } catch (e) {
      setError(e.message);
      setStep("idle");
    }
  }

  function toggleRetailer(name) {
    setSelected((s) => {
      const next = new Set(s);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  }

  async function handleConfirm() {
    setStep("launching");
    setError("");
    try {
      const result = await launchTask(uploadId, Array.from(selected));
      if (!result.upload_id || result.total_alis === 0) {
        setError("Nothing to launch for the selected lists.");
        setStep("reviewing");
        return;
      }
      onLaunchTask?.(result);
    } catch (e) {
      setError(e.message);
      setStep("reviewing");
    }
  }

  function handleCancel() {
    setStep("idle");
    setError("");
  }

  const selectedTotal = retailers
    .filter((r) => selected.has(r.name))
    .reduce((sum, r) => sum + r.needs_work_count, 0);

  if (step === "idle" || step === "loading-preview") {
    return (
      <div className="launch-task-bar">
        <div className="launch-task-copy">
          <span className="status-dot pending" />
          <span>Send records that still need a rooftop pin to Task Launcher.</span>
        </div>
        <div className="launch-task-actions">
          {error && <span className="launch-task-error">{error}</span>}
          <button onClick={handleOpenChecklist} disabled={!uploadId || step === "loading-preview"}>
            {step === "loading-preview" ? "Loading..." : "Launch Task"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="launch-task-bar expanded">
      <div className="launch-task-checklist-header">
        <span className="status-dot pending" />
        <span>Choose which lists to launch</span>
      </div>

      <div className="launch-task-checklist">
        {retailers.map((r) => {
          const isEmpty = r.needs_work_count === 0;
          return (
            <label key={r.name} className={isEmpty ? "checklist-row disabled" : "checklist-row"}>
              <input
                type="checkbox"
                checked={selected.has(r.name)}
                disabled={isEmpty}
                onChange={() => toggleRetailer(r.name)}
              />
              <span className="checklist-name">{r.name}</span>
              <span className="checklist-count">
                {isEmpty ? "nothing pending" : `${r.needs_work_count} need pinning`}
              </span>
            </label>
          );
        })}
      </div>

      <div className="launch-task-footer">
        <span className="launch-task-total">{selectedTotal} records selected</span>
        <div className="launch-task-actions">
          {error && <span className="launch-task-error">{error}</span>}
          <button className="secondary" onClick={handleCancel} disabled={step === "launching"}>
            Cancel
          </button>
          <button onClick={handleConfirm} disabled={selected.size === 0 || step === "launching"}>
            {step === "launching" ? "Launching..." : "Confirm & Launch"}
          </button>
        </div>
      </div>
    </div>
  );
}
