const BASE_URL = "http://localhost:8000/api/analyser";

export async function uploadAnalyserFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}

export async function uploadAnalyserFileWithMapping(file, mapping) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mapping", JSON.stringify(mapping));

  const res = await fetch(`${BASE_URL}/upload-with-mapping`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}

export async function launchTaskPreview(uploadId) {
  const res = await fetch(`${BASE_URL}/launch-task-preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ upload_id: uploadId }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Preview failed (${res.status})`);
  }
  return res.json();
}

export async function launchTask(uploadId, selectedRetailers) {
  const res = await fetch(`${BASE_URL}/launch-task`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      upload_id: uploadId,
      selected_retailers: selectedRetailers,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Launch task failed (${res.status})`);
  }
  return res.json();
}
