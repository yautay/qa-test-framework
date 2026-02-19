const TAG_FILE_NAME = "vrt-tags.json";

async function loadFromFile() {
  try {
    const response = await fetch(TAG_FILE_NAME, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.debug("unable to load tag file", error);
    return null;
  }
}

export async function loadTagSnapshot() {
  return await loadFromFile();
}

export async function saveTagSnapshotToFile(tagLog) {
  if (!tagLog || typeof tagLog !== "object") return false;
  try {
    const response = await fetch(TAG_FILE_NAME, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(tagLog, null, 2),
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}
