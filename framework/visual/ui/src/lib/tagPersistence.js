const TAG_FILE_NAME = "vrt-tags.json";

function buildTagFileUrl(runId) {
  const id = String(runId || "").trim();
  if (!id) return null;
  const encoded = encodeURIComponent(id);
  return `/reports/${encoded}/${TAG_FILE_NAME}`;
}

async function fetchJson(url) {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.debug("unable to load tag file", error);
    return null;
  }
}

async function putJson(url, payload) {
  try {
    const response = await fetch(url, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload, null, 2),
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}

export async function loadTagSnapshot(runId) {
  const url = buildTagFileUrl(runId);
  if (!url) return null;
  return await fetchJson(url);
}

export async function saveTagSnapshotToFile(tagLog, runId) {
  if (!tagLog || typeof tagLog !== "object") return false;
  const url = buildTagFileUrl(runId);
  if (!url) return false;
  return await putJson(url, tagLog);
}
