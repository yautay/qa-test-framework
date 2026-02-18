const TAG_FILE_NAME = "vrt-tags.json";
const LEGACY_STORAGE_KEY = "vrt-tag-log";

function storageKey() {
  const path = window?.location?.pathname || "default";
  return `${LEGACY_STORAGE_KEY}:${path}`;
}

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

function loadFromStorage() {
  try {
    const scopedStored = window?.localStorage?.getItem(storageKey());
    const stored = scopedStored || window?.localStorage?.getItem(LEGACY_STORAGE_KEY);
    if (!stored) return null;
    return JSON.parse(stored);
  } catch (error) {
    console.debug("unable to load tag log from storage", error);
    return null;
  }
}

export async function loadTagSnapshot() {
  const fromFile = await loadFromFile();
  const fromStorage = loadFromStorage();
  if (!fromFile && !fromStorage) return null;
  return { ...(fromFile || {}), ...(fromStorage || {}) };
}

export function persistTagSnapshot(tagLog) {
  if (!tagLog || typeof tagLog !== "object") return;
  try {
    window?.localStorage?.setItem(storageKey(), JSON.stringify(tagLog));
  } catch (error) {
    console.debug("unable to persist tag snapshot", error);
  }
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

export function downloadTagSnapshot(tagLog) {
  if (!tagLog || typeof tagLog !== "object") return;
  try {
    const json = JSON.stringify(tagLog, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = TAG_FILE_NAME;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.debug("unable to create tag snapshot export", error);
  }
}

export async function parseTagFile(file) {
  if (!file) return null;
  try {
    const text = await file.text();
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === "object") return parsed;
  } catch (error) {
    return null;
  }
  return null;
}
