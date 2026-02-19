import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../lib/api/reportsApi", () => ({
  fetchReportResults: vi.fn(),
  sendRunReport: vi.fn(),
}));

import ReportPage from "./ReportPage.vue";
import { fetchReportResults, sendRunReport } from "../lib/api/reportsApi";
import { createStore, filteredSorted } from "../lib/store";

function buildContext(overrides = {}) {
  const key = "scenario-1::actual.png::baseline.png::diff.png";
  return {
    prompt: { active: false, type: null },
    noteEditor: { active: false, rowKey: "", text: "", hasExisting: false },
    metadataPanel: { active: false, payload: {} },
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
    normalizeTagLog: ReportPage.methods.normalizeTagLog,
    persistTags: vi.fn(),
    downloadBugPdf: vi.fn(),
    buildMetadataPayload: ReportPage.methods.buildMetadataPayload,
    closeMetadataPanel: ReportPage.methods.closeMetadataPanel,
    cancelNoteEditor: ReportPage.methods.cancelNoteEditor,
    deactivateSuperZoom: vi.fn(),
    cancelPrompt: vi.fn(),
    isTagReported: ReportPage.methods.isTagReported,
    ...overrides,
  };
}

describe("ReportPage tag removal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

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

describe("ReportPage metadata panel", () => {
  it("opens metadata panel from table row", () => {
    const ctx = buildContext({ runId: "run-1" });
    const row = {
      scenario_id: "scenario-1",
      status: "failed",
      message: "boom",
      tester: "jan.k",
      run_note: "manual",
      test_metadata: { extra: { flag: true } },
    };

    ReportPage.methods.openMetadataFromTable.call(ctx, row, 2);

    expect(ctx.selectedIndex).toBe(2);
    expect(ctx.metadataPanel.active).toBe(true);
    expect(ctx.metadataPanel.payload.run.run_id).toBe("run-1");
    expect(ctx.metadataPanel.payload.run.tester).toBe("jan.k");
  });
});

describe("ReportPage report send", () => {
  it("opens send-report prompt when candidates exist", () => {
    const ctx = buildContext({
      runId: "run-1",
      reportCandidatesCount: 1,
      reportMessage: "",
    });

    ReportPage.methods.promptSendReport.call(ctx);

    expect(ctx.prompt).toEqual({ active: true, type: "send-report" });
  });

  it("sends report and refreshes tag snapshot", async () => {
    sendRunReport.mockResolvedValueOnce({
      bug: { sent: 1, failed: 0, skipped_locked: 0 },
      aso: { sent: 0, failed: 0, skipped_locked: 0 },
      pdf: { pages: 1 },
      tag_snapshot: {
        "scenario-1::actual.png::baseline.png::diff.png": {
          bug: true,
          aso: false,
          baseline: false,
          note: null,
          bug_reported: true,
          aso_reported: false,
          bug_reported_at: "2026-02-19T11:00:00Z",
          aso_reported_at: "",
        },
      },
    });

    const ctx = buildContext({
      runId: "run-1",
      reportMessage: "",
      normalizeTagLog: ReportPage.methods.normalizeTagLog,
    });

    await ReportPage.methods.executeSendReport.call(ctx);

    expect(sendRunReport).toHaveBeenCalledTimes(1);
    expect(ctx.viewer.tagLog["scenario-1::actual.png::baseline.png::diff.png"].bug_reported).toBe(true);
    expect(ctx.downloadBugPdf).toHaveBeenCalledTimes(1);
    expect(ctx.persistTags).toHaveBeenCalledTimes(1);
  });
});

describe("ReportPage loadResults", () => {
  it("clears selected index when fetched rows are empty", async () => {
    fetchReportResults.mockResolvedValueOnce([]);

    const ctx = {
      runId: "run-1",
      loadError: "",
      selectedIndex: 3,
      store: createStore(),
      viewer: { tagLog: {} },
    };
    Object.defineProperty(ctx, "rows", {
      get() {
        return filteredSorted(this.store, this.viewer.tagLog);
      },
    });

    await ReportPage.methods.loadResults.call(ctx);

    expect(ctx.selectedIndex).toBe(-1);
    expect(ctx.loadError).toBe("");
  });

  it("clears selected index on fetch error", async () => {
    fetchReportResults.mockRejectedValueOnce(new Error("boom"));

    const ctx = {
      runId: "run-1",
      loadError: "",
      selectedIndex: 2,
      store: createStore(),
      viewer: { tagLog: {} },
    };
    Object.defineProperty(ctx, "rows", {
      get() {
        return filteredSorted(this.store, this.viewer.tagLog);
      },
    });

    await ReportPage.methods.loadResults.call(ctx);

    expect(ctx.selectedIndex).toBe(-1);
    expect(ctx.loadError).toContain("Unable to load results: boom");
  });
});
