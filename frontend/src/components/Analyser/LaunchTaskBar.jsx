import { useState } from "react";
import { launchTask } from "../../api/analyser";
import "./LaunchTaskBar.css";

/**
 * Filters the analysed file down to records that still need work (Geo
 * Accuracy not yet rooftop-verified) and hands that subset straight to
 * Task Launcher's assignment screen - no re-upload needed.
 */
export default function LaunchTaskBar({ uploadId, onLaunchTask }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleClick() {
    if (!uploadId) return;
    setLoading(true);
    setError("");
    try {
      const result = await launchTask(uploadId);
      if (!result.upload_id || result.total_alis === 0) {
        setError("Nothing to launch - every record already has a verified rooftop pin.");
        return;
      }
      onLaunchTask?.(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="launch-task-bar">
      <div className="launch-task-copy">
        <span className="status-dot pending" />
        <span>Send records that still need a rooftop pin to Task Launcher.</span>
      </div>
      <div className="launch-task-actions">
        {error && <span className="launch-task-error">{error}</span>}
        <button onClick={handleClick} disabled={loading || !uploadId}>
          {loading ? "Preparing..." : "Launch Task"}
        </button>
      </div>
    </div>
  );
}
