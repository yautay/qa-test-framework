import { describe, expect, it } from "vitest";
import {
  NOTE_MAX_LENGTH,
  sanitizeNoteText,
  normalizeNoteDraft,
  normalizeNote,
  normalizeCaseStateSnapshot,
} from "./notes";

describe("notes.js", () => {
  describe("NOTE_MAX_LENGTH", () => {
    it("is 500", () => {
      expect(NOTE_MAX_LENGTH).toBe(500);
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

    it("preserves angle brackets for safe rendering", () => {
      expect(sanitizeNoteText("<script>alert(1)</script>")).toBe("<script>alert(1)</script>");
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

  describe("normalizeCaseStateSnapshot", () => {
    it("returns empty object for non-object input", () => {
      expect(normalizeCaseStateSnapshot(null)).toEqual({});
      expect(normalizeCaseStateSnapshot(undefined)).toEqual({});
      expect(normalizeCaseStateSnapshot("string")).toEqual({});
      expect(normalizeCaseStateSnapshot(123)).toEqual({});
    });

    it("normalizes case entries", () => {
      const snapshot = {
        "key1": {
          bug: { locked: "truthy", synced: 0, note: "note1" },
          aso: { locked: true, synced: "yes", note: "aso1" },
        },
      };

      const result = normalizeCaseStateSnapshot(snapshot);

      expect(result.key1.bug.locked).toBe(true);
      expect(result.key1.bug.synced).toBe(false);
      expect(result.key1.aso.locked).toBe(true);
      expect(result.key1.aso.synced).toBe(true);
      expect(result.key1.bug.note).toBe("note1");
      expect(result.key1.aso.note).toBe("aso1");
      expect(result.key1.baseline).toBe(false);
    });

    it("normalizes baseline flag", () => {
      const snapshot = {
        "key1": {
          bug: { locked: false, synced: false, note: "" },
          aso: { locked: false, synced: false, note: "" },
          baseline: 1,
        },
      };

      const result = normalizeCaseStateSnapshot(snapshot);

      expect(result.key1.baseline).toBe(true);
    });

    it("handles missing fields with defaults", () => {
      const snapshot = {
        "key1": { bug: { locked: true } },
      };

      const result = normalizeCaseStateSnapshot(snapshot);

      expect(result.key1.bug.locked).toBe(true);
      expect(result.key1.bug.synced).toBe(false);
      expect(result.key1.aso.locked).toBe(false);
      expect(result.key1.aso.synced).toBe(false);
      expect(result.key1.bug.note).toBe("");
      expect(result.key1.aso.note).toBe("");
    });

    it("skips non-object entries", () => {
      const snapshot = {
        "key1": { bug: { locked: true } },
        "key2": "invalid",
        "key3": null,
        "key4": 123,
      };

      const result = normalizeCaseStateSnapshot(snapshot);

      expect(result.key1).toBeDefined();
      expect(result.key2).toBeUndefined();
      expect(result.key3).toBeUndefined();
      expect(result.key4).toBeUndefined();
    });

    it("normalizes note content", () => {
      const snapshot = {
        "key1": {
          bug: { note: "  test  ", synced: true },
        },
      };

      const result = normalizeCaseStateSnapshot(snapshot);

      expect(result.key1.bug.note).toBe("test");
    });

    it("handles non-string note content", () => {
      const snapshot = {
        "key1": {
          bug: { note: 12345, synced: 1 },
        },
      };

      const result = normalizeCaseStateSnapshot(snapshot);

      expect(result.key1.bug.note).toBe("");
    });
  });
});
