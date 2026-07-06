import { useEffect, useState } from "react";
import UploadStep from "./UploadStep";
import MultiAssignStep from "./MultiAssignStep";
import SingleAssignStep from "./SingleAssignStep";
import { clearUpload } from "../../api/taskLauncher";
import "./TaskLauncher.css";

export default function TaskLauncher({ initialData, onInitialDataConsumed }) {
  const [uploadData, setUploadData] = useState(null); // {upload_id, mode, total_alis, retailer_counts}
  const [done, setDone] = useState(false);

  // If Analyser's "Launch Task" handed off pre-filtered data, load it
  // straight in - skipping the upload step entirely.
  useEffect(() => {
    if (initialData) {
      setUploadData(initialData);
      setDone(false);
      onInitialDataConsumed?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialData]);

  function handleUploaded(data) {
    setUploadData(data);
    setDone(false);
  }

  async function handleDone() {
    if (uploadData?.upload_id) {
      await clearUpload(uploadData.upload_id);
    }
    setDone(true);
  }

  function handleStartOver() {
    setUploadData(null);
    setDone(false);
  }

  return (
    <div className="task-launcher">
      <header className="task-launcher-header">
        <h1>Task Launcher</h1>
        {uploadData && (
          <button className="start-over-btn" onClick={handleStartOver}>
            Start over
          </button>
        )}
      </header>

      {!uploadData && <UploadStep onUploaded={handleUploaded} />}

      {uploadData && !done && uploadData.mode === "multi" && (
        <MultiAssignStep
          uploadId={uploadData.upload_id}
          retailerCounts={uploadData.retailer_counts}
          totalAlis={uploadData.total_alis}
          onDone={handleDone}
        />
      )}

      {uploadData && !done && uploadData.mode === "single" && (
        <SingleAssignStep
          uploadId={uploadData.upload_id}
          totalAlis={uploadData.total_alis}
          onDone={handleDone}
        />
      )}

      {done && (
        <div className="done-panel">
          <h2>Task generated</h2>
          <p>Your Excel file has been downloaded.</p>
          <button onClick={handleStartOver}>Launch another task</button>
        </div>
      )}
    </div>
  );
}
