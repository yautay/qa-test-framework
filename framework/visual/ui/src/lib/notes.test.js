import { describe, expect, it } from "vitest";
import {
  NOTE_MAX_LENGTH,
  sanitizeNoteText,
  normalizeNoteDraft,
  normalizeNote,
  normalizeTagLogSnapshot,
} from "./notes";

describe("notes.js", () => {
  describe("NOTE_MAX_LENGTH", () => {
    it("is 2000", () => {
      expect(NOTE_MAX_LENGTH).toBe(2000);
    });
  });

  describe("sanitizeNoteText", () => {
    it("returns empty string for non-string input", () => {
      expect(sanitizeNoteText(null)).toBe("");
      expect(sanitizeNoteText(undefined)).toBe("");
      expect(sanitizeNoteText(123)).toBe("");
      expect(sanitizeNoteText({})).toBe("");
      expect(sanitizeNoteText([])).toBe("");
    });

    it("trims whitespace", () => {
      expect(sanitizeNoteText("  hello  ")).toBe("hello");
      expect(sanitizeNoteText("\n\ttest\n\t")).toBe("test");
    });

    it("replaces Windows line endings", () => {
      expect(sanitizeNoteText("line1\r\nline2")).toBe("line1\nline2");
      expect(sanitizeNoteText("line1\rline2")).toBe("line1\nline2");
    });

    it("removes control characters", () => {
      expect(sanitizeNoteText("test\u0000")).toBe("test");
      expect(sanitizeNoteText("test\u0008")).toBe("test");
      expect(sanitizeNoteText("test\u000B")).toBe("test");
      expect(sanitizeNoteText("test\u000C")).toBe("test");
      expect(sanitizeNoteText("test\u000Etest")).toBe("testtest");
      expect(sanitizeNoteText("test\u001F")).toBe("test");
    });

    it("truncates to max length", () => {
      const longText = "a".repeat(3000);
      expect(sanitizeNoteText(longText).length).toBe(NOTE_MAX_LENGTH);
    });

    it("keeps valid text unchanged", () => {
      expect(sanitizeNoteText("Hello World")).toBe("Hello World");
      expect(sanitizeNoteText("Multi\nLine\nText")).toBe("Multi\nLine\nText");
    });
  });

  describe("normalizeNoteDraft", () => {
    it("returns empty string for non-string input", () => {
      expect(normalizeNoteDraft(null)).toBe("");
      expect(normalizeNoteDraft(undefined)).toBe("");
      expect(normalizeNoteDraft(123)).toBe("");
      expect(normalizeNoteDraft({})).toBe("");
    });

    it("does NOT trim whitespace (draft mode)", () => {
      expect(normalizeNoteDraft("  hello  ")).toBe("  hello  ");
    });

    it("replaces Windows line endings", () => {
      expect(normalizeNoteDraft("line1\r\nline2")).toBe("line1\nline2");
    });

    it("removes control characters", () => {
      expect(normalizeNoteDraft("test\u0000")).toBe("test");
    });

    it("truncates to max length", () => {
      const longText = "a".repeat(3000);
      expect(normalizeNoteDraft(longText).length).toBe(NOTE_MAX_LENGTH);
    });
  });

  describe("normalizeNote", () => {
    it("returns null for non-object input", () => {
      expect(normalizeNote(null)).toBeNull();
      expect(normalizeNote(undefined)).toBeNull();
      expect(normalizeNote("string")).toBeNull();
      expect(normalizeNote(123)).toBeNull();
    });

    it("returns null for empty text", () => {
      expect(normalizeNote({ text: "" })).toBeNull();
      expect(normalizeNote({ text: "   " })).toBeNull();
      expect(normalizeNote({ text: null })).toBeNull();
      expect(normalizeNote({ text: undefined })).toBeNull();
    });

    it("returns normalized note with text and updatedAt", () => {
      const input = { text: "  Test Note  ", updatedAt: "2026-01-01T12:00:00Z" };
      const result = normalizeNote(input);

      expect(result).not.toBeNull();
      expect(result.text).toBe("Test Note");
      expect(result.updatedAt).toBe("2026-01-01T12:00:00Z");
    });

    it("handles missing updatedAt", () => {
      const input = { text: "Test" };
      const result = normalizeNote(input);

      expect(result).not.toBeNull();
      expect(result.text).toBe("Test");
      expect(result.updatedAt).toBe("");
    });

    it("handles non-string updatedAt", () => {
      const input = { text: "Test", updatedAt: 12345 };
      const result = normalizeNote(input);

      expect(result).not.toBeNull();
      expect(result.updatedAt).toBe("");
    });
  });

  describe("normalizeTagLogSnapshot", () => {
    it("returns empty object for non-object input", () => {
      expect(normalizeTagLogSnapshot(null)).toEqual({});
      expect(normalizeTagLogSnapshot(undefined)).toEqual({});
      expect(normalizeTagLogSnapshot("string")).toEqual({});
      expect(normalizeTagLogSnapshot(123)).toEqual({});
    });

    it("normalizes tag entries", () => {
      const snapshot = {
        "key1": {
          bug: "truthy",
          aso: true,
          baseline: 1,
          note: { text: "note1", updatedAt: "2026-01-01" },
          bug_reported: "yes",
          note_reported: 0,
        },
      };

      const result = normalizeTagLogSnapshot(snapshot);

      expect(result.key1.bug).toBe(true);
      expect(result.key1.aso).toBe(true);
      expect(result.key1.baseline).toBe(true);
      expect(result.key1.note.text).toBe("note1");
      expect(result.key1.bug_reported).toBe(true);
      expect(result.key1.note_reported).toBe(false);
    });

    it("handles missing fields with defaults", () => {
      const snapshot = {
        "key1": { bug: true },
      };

      const result = normalizeTagLogSnapshot(snapshot);

      expect(result.key1.bug).toBe(true);
      expect(result.key1.aso).toBe(false);
      expect(result.key1.baseline).toBe(false);
      expect(result.key1.note).toBeNull();
      expect(result.key1.bug_reported).toBe(false);
      expect(result.key1.aso_reported).toBe(false);
      expect(result.key1.note_reported).toBe(false);
      expect(result.key1.bug_reported_at).toBe("");
      expect(result.key1.aso_reported_at).toBe("");
      expect(result.key1.note_reported_at).toBe("");
      expect(result.key1.note_reported_hash).toBe("");
    });

    it("skips non-object tag entries", () => {
      const snapshot = {
        "key1": { bug: true },
        "key2": "invalid",
        "key3": null,
        "key4": 123,
      };

      const result = normalizeTagLogSnapshot(snapshot);

      expect(result.key1).toBeDefined();
      expect(result.key2).toBeUndefined();
      expect(result.key3).toBeUndefined();
      expect(result.key4).toBeUndefined();
    });

    it("normalizes note field", () => {
      const snapshot = {
        "key1": {
          note: { text: "  test  ", updatedAt: "2026-01-01" },
        },
      };

      const result = normalizeTagLogSnapshot(snapshot);

      expect(result.key1.note.text).toBe("test");
      expect(result.key1.note.updatedAt).toBe("2026-01-01");
    });

    it("handles non-string timestamp fields", () => {
      const snapshot = {
        "key1": {
          bug_reported_at: 12345,
          aso_reported_at: null,
          note_reported_at: undefined,
        },
      };

      const result = normalizeTagLogSnapshot(snapshot);

      expect(result.key1.bug_reported_at).toBe("");
      expect(result.key1.aso_reported_at).toBe("");
      expect(result.key1.note_reported_at).toBe("");
    });
  });
});
