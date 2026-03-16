export const NOTE_MAX_LENGTH = 500;

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
  const normalizeSynced = (value) => {
    if (typeof value === "string") {
      const lowered = value.trim().toLowerCase();
      if (["true", "1", "yes", "y"].includes(lowered)) return true;
      if (["false", "0", "no", "n", ""].includes(lowered)) return false;
    }
    return !!value;
  };
  for (const [key, state] of Object.entries(snapshot)) {
    if (!state || typeof state !== "object") continue;
    const bug = state.bug && typeof state.bug === "object" ? state.bug : {};
    const aso = state.aso && typeof state.aso === "object" ? state.aso : {};
    const bugNote = sanitizeNoteText(bug.note || "");
    const asoNote = sanitizeNoteText(aso.note || "");
    normalized[key] = {
      bug: { locked: !!bug.locked, synced: normalizeSynced(bug.synced), note: bugNote },
      aso: { locked: !!aso.locked, synced: normalizeSynced(aso.synced), note: asoNote },
      baseline: !!state.baseline,
    };
  }
  return normalized;
}
