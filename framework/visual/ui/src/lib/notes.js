export const NOTE_MAX_LENGTH = 200;

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
  const raw = note.content !== undefined ? note.content : note.text;
  const text = sanitizeNoteText(raw);
  if (!text) return null;
  const updatedAt = typeof note.updatedAt === "string" ? note.updatedAt : "";
  return {
    text,
    updatedAt,
  };
}

export function normalizeCaseStateSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== "object") return {};
  const normalized = {};
  for (const [key, state] of Object.entries(snapshot)) {
    if (!state || typeof state !== "object") continue;
    const bug = state.bug && typeof state.bug === "object" ? state.bug : {};
    const aso = state.aso && typeof state.aso === "object" ? state.aso : {};
    const note = state.note && typeof state.note === "object" ? state.note : {};
    const content = sanitizeNoteText(note.content || "");
    normalized[key] = {
      bug: { locked: !!bug.locked, synced: !!bug.synced },
      aso: { locked: !!aso.locked, synced: !!aso.synced },
      note: { content, synced: !!note.synced },
    };
  }
  return normalized;
}
