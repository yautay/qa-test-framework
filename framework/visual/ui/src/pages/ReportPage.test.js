import { describe, expect, it, vi } from "vitest";

import ReportPage from "./ReportPage.vue";

function buildContext(overrides = {}) {
  const key = "scenario-1::actual.png::baseline.png::diff.png";
  return {
    prompt: { active: false, type: null },
    noteEditor: { active: false, rowKey: "", text: "", hasExisting: false },
    viewer: {
      modalRow: {
        scenario_id: "scenario-1",
        actual_path: "actual.png",
        baseline_path: "baseline.png",
        diff_path: "diff.png",
      },
      tagLog: {
        [key]: { bug: true, aso: false, baseline: false, note: null },
      },
      tags: { bug: true, aso: false, baseline: false, note: null },
      tagLocked: {
        [key]: { bug: true, aso: false, baseline: false },
      },
      modal: { hide: vi.fn() },
    },
    rows: [],
    selectedIndex: -1,
    getRowTagKey: vi.fn(() => key),
    noteForRow: vi.fn(() => null),
    ensureTagEntry: vi.fn(() => ({
      key,
      entry: { bug: true, aso: false, baseline: false, note: null },
    })),
    sanitizeNoteText: ReportPage.methods.sanitizeNoteText,
    normalizeNoteDraft: ReportPage.methods.normalizeNoteDraft,
    persistTags: vi.fn(),
    cancelNoteEditor: ReportPage.methods.cancelNoteEditor,
    deactivateSuperZoom: vi.fn(),
    cancelPrompt: vi.fn(),
    ...overrides,
  };
}

describe("ReportPage tag removal", () => {
  it("allows opening remove prompt even for locked tag", () => {
    const ctx = buildContext({
      isTagLocked: vi.fn(() => true),
    });

    ReportPage.methods.promptRemoveTag.call(ctx, "bug");

    expect(ctx.prompt).toEqual({ active: true, type: "remove-bug" });
  });

  it("clears tag value and unlocks it when removing", () => {
    const ctx = buildContext();

    ReportPage.methods.removeTag.call(ctx, "bug");

    const key = ctx.getRowTagKey.mock.results[0].value;
    expect(ctx.viewer.tagLog[key].bug).toBe(false);
    expect(ctx.viewer.tags.bug).toBe(false);
    expect(ctx.viewer.tagLocked[key].bug).toBe(false);
    expect(ctx.persistTags).toHaveBeenCalledTimes(1);
  });
});

describe("ReportPage note editor", () => {
  it("opens note editor for current row", () => {
    const ctx = buildContext({
      noteForRow: vi.fn(() => ({ text: "Investigate", updatedAt: "2026-02-19T12:00:00.000Z" })),
    });

    ReportPage.methods.openNoteEditor.call(ctx);

    expect(ctx.noteEditor.active).toBe(true);
    expect(ctx.noteEditor.text).toBe("Investigate");
    expect(ctx.noteEditor.hasExisting).toBe(true);
  });

  it("saves note and persists snapshot", () => {
    const entry = { bug: true, aso: false, baseline: false, note: null };
    const ctx = buildContext({
      noteEditor: { active: true, rowKey: "k", text: "  Keep this  ", hasExisting: false },
      ensureTagEntry: vi.fn(() => ({ key: "k", entry })),
    });

    ReportPage.methods.saveNoteFromEditor.call(ctx);

    expect(entry.note.text).toBe("Keep this");
    expect(typeof entry.note.updatedAt).toBe("string");
    expect(ctx.persistTags).toHaveBeenCalledTimes(1);
    expect(ctx.noteEditor.active).toBe(false);
  });

  it("deletes note immediately and persists snapshot", () => {
    const entry = { bug: true, aso: false, baseline: false, note: { text: "Old" } };
    const ctx = buildContext({
      noteEditor: { active: true, rowKey: "k", text: "Old", hasExisting: true },
      ensureTagEntry: vi.fn(() => ({ key: "k", entry })),
    });

    ReportPage.methods.deleteNoteFromEditor.call(ctx);

    expect(entry.note).toBeNull();
    expect(ctx.persistTags).toHaveBeenCalledTimes(1);
    expect(ctx.noteEditor.active).toBe(false);
  });

  it("ignores global shortcuts when note editor is active", () => {
    const ctx = buildContext({
      noteEditor: { active: true, rowKey: "k", text: "a", hasExisting: true },
      navigate: vi.fn(),
      openNoteEditor: vi.fn(),
    });
    const evt = { key: "A", code: "KeyA", preventDefault: vi.fn() };

    ReportPage.methods.handleKeydown.call(ctx, evt);

    expect(ctx.navigate).not.toHaveBeenCalled();
    expect(ctx.openNoteEditor).not.toHaveBeenCalled();
  });
});
