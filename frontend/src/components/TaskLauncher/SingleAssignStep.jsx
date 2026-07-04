import { useEffect, useState } from "react";
import { getTarget, generateSingle } from "../../api/taskLauncher";
import "./SingleAssignStep.css";

export default function SingleAssignStep({ uploadId, totalAlis, onDone }) {
  const [analystNames, setAnalystNames] = useState(["Analyst 1", "Analyst 2"]);
  const [newAnalystName, setNewAnalystName] = useState("");
  const [taskName, setTaskName] = useState("");
  const [target, setTarget] = useState(null);
  const [remainder, setRemainder] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    getTarget(uploadId, analystNames.length)
      .then((res) => {
        if (!cancelled) {
          setTarget(res.target);
          setRemainder(res.remainder);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [uploadId, analystNames.length]);

  function addAnalyst() {
    const name = newAnalystName.trim();
    if (!name || analystNames.includes(name)) return;
    setAnalystNames((names) => [...names, name]);
    setNewAnalystName("");
  }

  function removeAnalyst(name) {
    setAnalystNames((names) => names.filter((n) => n !== name));
  }

  async function handleGenerate() {
    setError("");
    if (analystNames.length === 0) {
      setError("Add at least one analyst.");
      return;
    }
    setGenerating(true);
    try {
      await generateSingle({ uploadId, analystNames, taskName });
      onDone?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="single-assign">
      <h2>Split evenly</h2>
      <p className="single-assign-hint">
        {totalAlis} total records, single retailer - split equally across analysts.
      </p>

      <div className="analyst-manager">
        {analystNames.map((name) => (
          <span className="analyst-chip" key={name}>
            {name}
            <button onClick={() => removeAnalyst(name)} title="Remove analyst">
              ×
            </button>
          </span>
        ))}
        <input
          placeholder="Add analyst name"
          value={newAnalystName}
          onChange={(e) => setNewAnalystName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addAnalyst()}
        />
        <button onClick={addAnalyst}>Add</button>
      </div>

      {target !== null && (
        <p className="target-line">
          Each analyst gets {target} records
          {remainder ? ` (first analyst gets ${remainder} extra)` : ""}.
        </p>
      )}

      <label className="task-name-label">
        Task name
        <input value={taskName} onChange={(e) => setTaskName(e.target.value)} placeholder="e.g. Week 27 TJX" />
      </label>

      {error && <div className="assign-error">{error}</div>}

      <button className="generate-btn" disabled={generating} onClick={handleGenerate}>
        {generating ? "Generating..." : "Generate Excel"}
      </button>
    </div>
  );
}
