export const NOTE_MAX_LENGTH = 2000;

const NOTE_CONTROL_CHAR_REGEX = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g;

export function sanitizeNoteText(raw) {
  if (typeof raw !== "string") return "";
  return raw
    .replace(/\r\n?/g, "\n")
    .replace(NOTE_CONTROL_CHAR_REGEX, "")
    .trim()
    .slice(0, NOTE_MAX_LENGTH);
}

export function normalizeNoteDraft(raw) {
  if (typeof raw !== "string") return "";
  return raw
    .replace(/\r\n?/g, "\n")
    .replace(NOTE_CONTROL_CHAR_REGEX, "")
    .slice(0, NOTE_MAX_LENGTH);
}

export function normalizeNote(note) {
  if (!note || typeof note !== "object") return null;
  const text = sanitizeNoteText(note.text);
  if (!text) return null;
  const updatedAt = typeof note.updatedAt === "string" ? note.updatedAt : "";
  return {
    text,
    updatedAt,
  };
}

export function normalizeTagLogSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== "object") return {};
  const normalized = {};
  for (const [key, tags] of Object.entries(snapshot)) {
    if (!tags || typeof tags !== "object") continue;
    normalized[key] = {
      bug: !!tags.bug,
      aso: !!tags.aso,
      baseline: !!tags.baseline,
      note: normalizeNote(tags.note),
      bug_reported: !!tags.bug_reported,
      aso_reported: !!tags.aso_reported,
      note_reported: !!tags.note_reported,
      bug_reported_at: typeof tags.bug_reported_at === "string" ? tags.bug_reported_at : "",
      aso_reported_at: typeof tags.aso_reported_at === "string" ? tags.aso_reported_at : "",
      note_reported_at: typeof tags.note_reported_at === "string" ? tags.note_reported_at : "",
      note_reported_hash: typeof tags.note_reported_hash === "string" ? tags.note_reported_hash : "",
    };
  }
  return normalized;
}
