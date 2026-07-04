import { useState } from "react";
import AnalyserUploadStep from "./AnalyserUploadStep";
import ResultsDashboard from "./ResultsDashboard";
import "./Analyser.css";

export default function Analyser() {
  const [data, setData] = useState(null); // {row_count, results}

  function handleStartOver() {
    setData(null);
  }

  return (
    <div className="analyser">
      <header className="analyser-header">
        <h1>Analyser</h1>
        {data && (
          <button className="start-over-btn" onClick={handleStartOver}>
            Analyse another file
          </button>
        )}
      </header>

      {!data && <AnalyserUploadStep onUploaded={setData} />}
      {data && <ResultsDashboard results={data.results} />}
    </div>
  );
}
