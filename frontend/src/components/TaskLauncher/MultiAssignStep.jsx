import { useEffect, useMemo, useState } from "react";
import BalanceTracker from "./BalanceTracker";
import { getTarget, generateMulti } from "../../api/taskLauncher";
import "./MultiAssignStep.css";

const SPLIT = "Split";

export default function MultiAssignStep({ uploadId, retailerCounts, totalAlis, onDone }) {
  const retailers = useMemo(() => Object.keys(retailerCounts), [retailerCounts]);

  const [analystNames, setAnalystNames] = useState(["Analyst 1", "Analyst 2"]);
  const [newAnalystName, setNewAnalystName] = useState("");
  const [assignments, setAssignments] = useState({}); // retailer -> analystName | "Split"
  const [splitCounts, setSplitCounts] = useState({}); // retailer -> {analystName: count}
  const [selected, setSelected] = useState(new Set()); // bulk-select
  const [bulkTarget, setBulkTarget] = useState("");
  const [taskName, setTaskName] = useState("");
  const [target, setTarget] = useState(null);
  const [remainder, setRemainder] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  // Only hits the backend when the analyst COUNT changes - not per click.
  useEffect(() => {
    let cancelled = false;
    getTarget(uploadId, analystNames.length)
      .then((res) => {
        if (!cancelled) {
          setTarget(res.target);
          setRemainder(res.remainder);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setTarget(null);
          setRemainder(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [uploadId, analystNames.length]);

  // Everything below is pure client-side computation - instant, no network.
  const assignedCounts = useMemo(() => {
    const counts = Object.fromEntries(analystNames.map((n) => [n, 0]));
    for (const retailer of retailers) {
      const assignment = assignments[retailer];
      if (!assignment) continue;
      if (assignment === SPLIT) {
        const splits = splitCounts[retailer] || {};
        for (const [name, count] of Object.entries(splits)) {
          if (counts[name] !== undefined) counts[name] += Number(count) || 0;
        }
      } else if (counts[assignment] !== undefined) {
        counts[assignment] += retailerCounts[retailer];
      }
    }
    return counts;
  }, [assignments, splitCounts, analystNames, retailers, retailerCounts]);

  function addAnalyst() {
    const name = newAnalystName.trim();
    if (!name || analystNames.includes(name)) return;
    setAnalystNames((names) => [...names, name]);
    setNewAnalystName("");
  }

  function removeAnalyst(name) {
    setAnalystNames((names) => names.filter((n) => n !== name));
    setAssignments((a) => {
      const next = { ...a };
      for (const r of Object.keys(next)) if (next[r] === name) delete next[r];
      return next;
    });
  }

  function assignRetailer(retailer, value) {
    setAssignments((a) => ({ ...a, [retailer]: value }));
  }

  function toggleSelected(retailer) {
    setSelected((s) => {
      const next = new Set(s);
      next.has(retailer) ? next.delete(retailer) : next.add(retailer);
      return next;
    });
  }

  function applyBulkAssign() {
    if (!bulkTarget || selected.size === 0) return;
    setAssignments((a) => {
      const next = { ...a };
      for (const r of selected) next[r] = bulkTarget;
      return next;
    });
    setSelected(new Set());
  }

  function updateSplitCount(retailer, analystName, value) {
    setSplitCounts((sc) => ({
      ...sc,
      [retailer]: { ...(sc[retailer] || {}), [analystName]: value },
    }));
  }

  function splitSum(retailer) {
    const splits = splitCounts[retailer] || {};
    return Object.values(splits).reduce((sum, v) => sum + (Number(v) || 0), 0);
  }

  const unassignedCount = retailers.filter((r) => !assignments[r]).length;

  async function handleGenerate() {
    setError("");

    if (unassignedCount > 0) {
      setError(`${unassignedCount} retailer(s) still unassigned.`);
      return;
    }
    for (const r of retailers) {
      if (assignments[r] === SPLIT && splitSum(r) !== retailerCounts[r]) {
        setError(`Split counts for "${r}" must add up to ${retailerCounts[r]} (currently ${splitSum(r)}).`);
        return;
      }
    }

    setGenerating(true);
    try {
      await generateMulti({
        uploadId,
        analystNames,
        retailerAssignments: assignments,
        splitCounts: Object.fromEntries(
          Object.entries(splitCounts).map(([r, m]) => [
            r,
            Object.fromEntries(Object.entries(m).map(([n, v]) => [n, Number(v) || 0])),
          ])
        ),
        taskName,
      });
      onDone?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="multi-assign">
      <div className="multi-assign-main">
        <h2>Assign retailers</h2>
        <p className="multi-assign-hint">
          {totalAlis} total records across {retailers.length} retailers.
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

        <div className="bulk-bar">
          <span>{selected.size} selected</span>
          <select value={bulkTarget} onChange={(e) => setBulkTarget(e.target.value)}>
            <option value="">Assign selected to...</option>
            {analystNames.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
            <option value={SPLIT}>Split</option>
          </select>
          <button disabled={!bulkTarget || selected.size === 0} onClick={applyBulkAssign}>
            Apply
          </button>
        </div>

        <table className="retailer-table">
          <thead>
            <tr>
              <th></th>
              <th>Retailer</th>
              <th>Records</th>
              <th>Assign to</th>
              <th>Split detail</th>
            </tr>
          </thead>
          <tbody>
            {retailers.map((retailer) => (
              <tr key={retailer}>
                <td>
                  <input
                    type="checkbox"
                    checked={selected.has(retailer)}
                    onChange={() => toggleSelected(retailer)}
                  />
                </td>
                <td>{retailer}</td>
                <td>{retailerCounts[retailer]}</td>
                <td>
                  <select
                    value={assignments[retailer] || ""}
                    onChange={(e) => assignRetailer(retailer, e.target.value)}
                  >
                    <option value="">— unassigned —</option>
                    {analystNames.map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                    <option value={SPLIT}>Split</option>
                  </select>
                </td>
                <td>
                  {assignments[retailer] === SPLIT && (
                    <div className="split-inputs">
                      {analystNames.map((n) => (
                        <label key={n}>
                          {n}
                          <input
                            type="number"
                            min="0"
                            value={(splitCounts[retailer] || {})[n] || ""}
                            onChange={(e) => updateSplitCount(retailer, n, e.target.value)}
                          />
                        </label>
                      ))}
                      <span
                        className={
                          splitSum(retailer) === retailerCounts[retailer] ? "split-ok" : "split-bad"
                        }
                      >
                        {splitSum(retailer)} / {retailerCounts[retailer]}
                      </span>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="multi-assign-sidebar">
        <h3>Balance</h3>
        {target !== null && (
          <p className="target-line">
            Target: {target} each{remainder ? ` (+${remainder} remainder)` : ""}
          </p>
        )}
        <BalanceTracker analysts={analystNames} assignedCounts={assignedCounts} target={target || 0} />

        <label className="task-name-label">
          Task name
          <input value={taskName} onChange={(e) => setTaskName(e.target.value)} placeholder="e.g. Week 27 TJX" />
        </label>

        {error && <div className="assign-error">{error}</div>}

        <button className="generate-btn" disabled={generating} onClick={handleGenerate}>
          {generating ? "Generating..." : "Generate Excel"}
        </button>
      </div>
    </div>
  );
}
