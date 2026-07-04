import { useState } from "react";
import { uploadAnalyserFile, uploadAnalyserFileWithMapping } from "../../api/analyser";
import "../TaskLauncher/UploadStep.css";

export default function AnalyserUploadStep({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mappingNeeded, setMappingNeeded] = useState(null);
  const [mapping, setMapping] = useState({});

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const result = await uploadAnalyserFile(file);
      if (result.needs_mapping) {
        setMappingNeeded(result);
      } else {
        onUploaded(result);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleMappingSubmit() {
    setLoading(true);
    setError("");
    try {
      const result = await uploadAnalyserFileWithMapping(file, mapping);
      onUploaded(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (mappingNeeded) {
    return (
      <div className="upload-step">
        <h2>Match your columns</h2>
        <p className="upload-hint">
          These required columns weren't found by name. Pick which column in your file matches each one.
        </p>
        {mappingNeeded.missing_columns.map((col) => (
          <div className="mapping-row" key={col}>
            <span className="mapping-required">{col}</span>
            <select
              value={mapping[col] || ""}
              onChange={(e) => setMapping((m) => ({ ...m, [col]: e.target.value }))}
            >
              <option value="">— choose column —</option>
              {mappingNeeded.available_columns.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        ))}
        {error && <div className="upload-error">{error}</div>}
        <button
          disabled={loading || Object.keys(mapping).length < mappingNeeded.missing_columns.length}
          onClick={handleMappingSubmit}
        >
          {loading ? "Applying..." : "Apply mapping & continue"}
        </button>
      </div>
    );
  }

  return (
    <div className="upload-step">
      <h2>Upload task list to analyse</h2>
      <p className="upload-hint">Choose the Excel or CSV file for this list.</p>
      <input
        type="file"
        accept=".xlsx,.xls,.csv"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      {error && <div className="upload-error">{error}</div>}
      <button disabled={!file || loading} onClick={handleUpload}>
        {loading ? "Analysing..." : "Upload & Analyse"}
      </button>
    </div>
  );
}
