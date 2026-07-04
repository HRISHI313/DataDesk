const BASE_URL = "http://localhost:8000/api/task-launcher";

/**
 * Uploads the task list file. Backend parses it once and caches the
 * DataFrame under an upload_id - everything after this (assign, split,
 * balance tracking) happens in the browser with zero more backend calls,
 * until Generate.
 */
export async function uploadTaskFile(file) {
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

export async function uploadTaskFileWithMapping(file, mapping) {
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

export async function getTarget(uploadId, numAnalysts) {
  const params = new URLSearchParams({
    upload_id: uploadId,
    num_analysts: String(numAnalysts),
  });
  const res = await fetch(`${BASE_URL}/target?${params.toString()}`);

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Target calculation failed (${res.status})`);
  }
  return res.json();
}

async function downloadGeneratedFile(res) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Generate failed (${res.status})`);
  }

  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : "TaskList.xlsx";

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function generateSingle({ uploadId, analystNames, taskName }) {
  const res = await fetch(`${BASE_URL}/single/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      upload_id: uploadId,
      analyst_names: analystNames,
      task_name: taskName || "",
    }),
  });
  await downloadGeneratedFile(res);
}

export async function generateMulti({
  uploadId,
  analystNames,
  retailerAssignments,
  splitCounts,
  taskName,
}) {
  const res = await fetch(`${BASE_URL}/multi/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      upload_id: uploadId,
      analyst_names: analystNames,
      retailer_assignments: retailerAssignments,
      split_counts: splitCounts || {},
      task_name: taskName || "",
    }),
  });
  await downloadGeneratedFile(res);
}

export async function clearUpload(uploadId) {
  await fetch(`${BASE_URL}/${uploadId}`, { method: "DELETE" });
}
