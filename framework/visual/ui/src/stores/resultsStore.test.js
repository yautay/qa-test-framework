import { describe, expect, it, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useResultsStore } from "./resultsStore";

describe("resultsStore", () => {
  let pinia;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
  });

  describe("setRows", () => {
    it("sets rows and updates summary", () => {
      const store = useResultsStore();
      const rows = [
        { scenario_id: "s1", status: "passed" },
        { scenario_id: "s2", status: "failed" },
        { scenario_id: "s3", status: "passed" },
      ];

      store.setRows(rows);

      expect(store.rows).toHaveLength(3);
      expect(store.summary.total).toBe(3);
      expect(store.summary.passed).toBe(2);
      expect(store.summary.failed).toBe(1);
    });

    it("normalizes new status to failed", () => {
      const store = useResultsStore();
      const rows = [
        { scenario_id: "s1", status: "new" },
      ];

      store.setRows(rows);

      expect(store.rows[0].status).toBe("failed");
      expect(store.summary.failed).toBe(1);
    });

    it("handles non-array input", () => {
      const store = useResultsStore();

      store.setRows(null);
      expect(store.rows).toEqual([]);

      store.setRows(undefined);
      expect(store.rows).toEqual([]);

      store.setRows("not an array");
      expect(store.rows).toEqual([]);
    });
  });

  describe("filteredSorted", () => {
    it("returns all rows when no filters applied", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "a", status: "passed" },
        { scenario_id: "b", status: "failed" },
      ]);

      const result = store.filteredSorted;

      expect(result).toHaveLength(2);
    });

    it("filters by query in scenario_id", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "login-test", status: "passed" },
        { scenario_id: "logout-test", status: "passed" },
        { scenario_id: "profile-test", status: "failed" },
      ]);
      store.q = "login";

      const result = store.filteredSorted;

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("login-test");
    });

    it("filters by query in message", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", message: "timeout error" },
        { scenario_id: "s2", message: "success" },
      ]);
      store.q = "timeout";

      const result = store.filteredSorted;

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("s1");
    });

    it("filters by status", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", status: "passed" },
        { scenario_id: "s2", status: "failed" },
        { scenario_id: "s3", status: "failed" },
      ]);
      store.status = "failed";

      const result = store.filteredSorted;

      expect(result).toHaveLength(2);
      expect(result.every(r => r.status === "failed")).toBe(true);
    });

    it("filters by viewport", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", viewport: "fhd" },
        { scenario_id: "s2", viewport: "2k" },
        { scenario_id: "s3", viewport: "fhd" },
      ]);
      store.viewport = "fhd";

      const result = store.filteredSorted;

      expect(result).toHaveLength(2);
      expect(result.every(r => r.viewport === "fhd")).toBe(true);
    });

    it("filters by browser", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", browser: "chromium" },
        { scenario_id: "s2", browser: "firefox" },
        { scenario_id: "s3", browser: "chromium" },
      ]);
      store.browser = "chromium";

      const result = store.filteredSorted;

      expect(result).toHaveLength(2);
      expect(result.every(r => r.browser === "chromium")).toBe(true);
    });

    it("combines multiple filters", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", status: "passed" },
        { scenario_id: "s2", status: "failed" },
        { scenario_id: "s3", status: "failed" },
      ]);
      store.status = "failed";
      store.q = "s3";

      const result = store.filteredSorted;

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("s3");
    });

    it("sorts by scenario_id ascending by default", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "z-test" },
        { scenario_id: "a-test" },
        { scenario_id: "m-test" },
      ]);

      const result = store.filteredSorted;

      expect(result[0].scenario_id).toBe("a-test");
      expect(result[1].scenario_id).toBe("m-test");
      expect(result[2].scenario_id).toBe("z-test");
    });

    it("sorts numerically descending for numeric keys", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", lpips: 0.1 },
        { scenario_id: "s2", lpips: 1.0 },
        { scenario_id: "s3", lpips: 0.01 },
      ]);
      store.sortKey = "lpips";

      const result = store.filteredSorted;

      expect(result[0].lpips).toBe(1.0);
      expect(result[1].lpips).toBe(0.1);
      expect(result[2].lpips).toBe(0.01);
    });

    it("sorts status by priority (failed, skipped, passed)", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", status: "passed" },
        { scenario_id: "s2", status: "failed" },
        { scenario_id: "s3", status: "skipped" },
      ]);
      store.sortKey = "status";

      const result = store.filteredSorted;

      expect(result[0].status).toBe("failed");
      expect(result[1].status).toBe("skipped");
      expect(result[2].status).toBe("passed");
    });

    it("trims query whitespace", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "test-a" },
        { scenario_id: "test-b" },
      ]);
      store.q = "  test-a  ";

      const result = store.filteredSorted;

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("test-a");
    });

    it("searches case-insensitively", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "Login-Test" },
        { scenario_id: "logout-test" },
      ]);
      store.q = "LOGIN";

      const result = store.filteredSorted;

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("Login-Test");
    });

    it("handles null values in sort", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", lpips: 0.5 },
        { scenario_id: "s2" },
        { scenario_id: "s3", lpips: null },
      ]);
      store.sortKey = "lpips";

      const result = store.filteredSorted;

      expect(result[0].scenario_id).toBe("s1");
    });
  });

  describe("resetFilters", () => {
    it("resets all filters to default", () => {
      const store = useResultsStore();
      store.q = "search";
      store.status = "failed";
      store.viewport = "fhd";
      store.browser = "chromium";
      store.sortKey = "lpips";

      store.resetFilters();

      expect(store.q).toBe("");
      expect(store.status).toBe("");
      expect(store.viewport).toBe("");
      expect(store.browser).toBe("");
      expect(store.sortKey).toBe("scenario_id");
    });
  });

  describe("setFilter", () => {
    it("sets individual filter values", () => {
      const store = useResultsStore();
      store.setFilter("q", "test");
      store.setFilter("status", "failed");

      expect(store.q).toBe("test");
      expect(store.status).toBe("failed");
    });
  });

  describe("viewports and browsers getters", () => {
    it("extracts unique viewports from rows", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", viewport: "fhd" },
        { scenario_id: "s2", viewport: "2k" },
        { scenario_id: "s3", viewport: "fhd" },
      ]);

      expect(store.viewports).toEqual(["2k", "fhd"]);
    });

    it("extracts unique browsers from rows", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", browser: "chromium" },
        { scenario_id: "s2", browser: "firefox" },
        { scenario_id: "s3", browser: "chromium" },
      ]);

      expect(store.browsers).toEqual(["chromium", "firefox"]);
    });
  });

  describe("toggleBaseline and setBaseline", () => {
    it("toggles baseline and updates tagLog", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.openViewer(store.rows[0], "test", 0);

      store.toggleBaseline();

      const key = "s1::a.png::::";
      expect(store.tagLog[key].baseline).toBe(true);
      expect(store.currentTags.baseline).toBe(true);
    });

    it("sets baseline explicitly", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.openViewer(store.rows[0], "test", 0);

      store.setBaseline(true);

      const key = "s1::a.png::::";
      expect(store.tagLog[key].baseline).toBe(true);
    });

    it("isTagLocked returns correct value", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.openViewer(store.rows[0], "test", 0);
      store.setBaseline(true);
      store.updateTagLog({
        "s1::a.png::::": { bug: { locked: true, synced: false } },
      });

      expect(store.isTagLocked("bug")).toBe(true);
      expect(store.isTagLocked("aso")).toBe(false);
      expect(store.isTagLocked("baseline")).toBe(false);
    });
  });

  describe("applyServerState", () => {
    it("updates pending and errors based on outbox", () => {
      const store = useResultsStore();
      const caseKey = "s1::img.png::::";

      store.applyServerState({
        test_cases: {
          [caseKey]: {
            bug: { locked: true, synced: false, note: "" },
            aso: { locked: false, synced: false, note: "" },
          },
        },
        outbox: [
          { test_case_id: caseKey, type: "BUG_SET", status: "pending" },
          {
            test_case_id: caseKey,
            type: "ASO_SET",
            status: "failed",
            last_error: "timeout",
            last_attempt_at: "2026-02-21T12:00:00Z",
          },
        ],
      });

      expect(store.pendingTags[caseKey].bug).toBe(true);
      expect(store.syncErrors[caseKey].message).toBe("timeout");
    });

    it("keeps pending when last_attempt_at predates retry marker", () => {
      const store = useResultsStore();
      const caseKey = "retry::case";
      store.setPendingTag(caseKey, "bug");
      const marker = store.retryMarkers[caseKey].bug;
      const older = new Date(marker - 1000).toISOString();

      store.updateSyncIndicatorsFromOutbox([
        {
          test_case_id: caseKey,
          type: "BUG_SET",
          status: "failed",
          last_error: "old failure",
          last_attempt_at: older,
        },
      ]);

      expect(store.pendingTags[caseKey].bug).toBe(true);
      expect(store.syncErrors[caseKey]).toBeUndefined();
    });

    it("shows error when failure timestamp is newer than retry marker", () => {
      const store = useResultsStore();
      const caseKey = "retry::case2";
      store.setPendingTag(caseKey, "bug");
      const marker = store.retryMarkers[caseKey].bug;
      const newer = new Date(marker + 1000).toISOString();

      store.updateSyncIndicatorsFromOutbox([
        {
          test_case_id: caseKey,
          type: "BUG_SET",
          status: "failed",
          last_error: "still bad",
          last_attempt_at: newer,
        },
      ]);

      expect(store.pendingTags[caseKey]).toBeUndefined();
      expect(store.syncErrors[caseKey].message).toBe("still bad");
    });
  });

  describe("updateTagLog", () => {
    it("normalizes tag log structure", () => {
      const store = useResultsStore();
      const snapshot = {
        "s1::a.png::::": {
          bug: { locked: true, synced: false, note: "test" },
        },
      };

      store.updateTagLog(snapshot);

      expect(store.tagLog["s1::a.png::::"].bug.locked).toBe(true);
      expect(store.tagLog["s1::a.png::::"].bug.note).toBe("test");
    });

    it("handles null/undefined input", () => {
      const store = useResultsStore();
      store.tagLog = { "test": { bug: { locked: true, synced: false } } };

      store.updateTagLog(null);
      expect(store.tagLog).toEqual({});

      store.tagLog = { "test": { bug: { locked: true, synced: false } } };
      store.updateTagLog(undefined);
      expect(store.tagLog).toEqual({});
    });
  });

  describe("baselineCandidates", () => {
    it("returns rows with baseline tag and actual_path", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
        { scenario_id: "s2", actual_path: "b.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { baseline: true },
        "s2::b.png::::": { baseline: false },
      };

      const candidates = store.baselineCandidates;

      expect(candidates).toHaveLength(1);
      expect(candidates[0].scenario_id).toBe("s1");
    });
  });

  describe("reportCandidatesCount", () => {
    it("counts rows with unsent bugs", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
        { scenario_id: "s2", actual_path: "b.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: { locked: true, synced: false } },
        "s2::b.png::::": { bug: { locked: false, synced: false } },
      };

      expect(store.reportCandidatesCount).toBe(1);
    });

    it("counts rows with unsent asos", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { aso: { locked: true, synced: false } },
      };

      expect(store.reportCandidatesCount).toBe(1);
    });

    it("does not count already synced bugs", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: { locked: true, synced: true } },
      };

      expect(store.reportCandidatesCount).toBe(0);
    });

    it("does not count already synced asos", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { aso: { locked: true, synced: true } },
      };

      expect(store.reportCandidatesCount).toBe(0);
    });

  });

  describe("hasAnyBug", () => {
    it("returns count of rows with bug tag", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png" },
        { scenario_id: "s2", actual_path: "b.png" },
        { scenario_id: "s3", actual_path: "c.png" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: { locked: true, synced: false } },
        "s2::b.png::::": { bug: { locked: false, synced: false } },
        "s3::c.png::::": { bug: { locked: true, synced: true } },
      };

      expect(store.hasAnyBug).toBe(2);
    });

    it("returns 0 when no bugs", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: { locked: false, synced: false } },
      };

      expect(store.hasAnyBug).toBe(0);
    });

    it("counts bugs regardless of synced status", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: { locked: true, synced: true } },
      };

      expect(store.hasAnyBug).toBe(1);
    });
  });

  describe("filtersActive", () => {
    it("returns false when no filters active", () => {
      const store = useResultsStore();
      store.setRows([{ scenario_id: "s1" }]);
      store.q = "";
      store.status = "";
      store.viewport = "";
      store.browser = "";

      expect(store.filtersActive).toBe(false);
    });

    it("returns true when q filter active", () => {
      const store = useResultsStore();
      store.setRows([{ scenario_id: "s1" }]);
      store.q = "test";

      expect(store.filtersActive).toBe(true);
    });

    it("returns true when status filter active", () => {
      const store = useResultsStore();
      store.setRows([{ scenario_id: "s1" }]);
      store.status = "failed";

      expect(store.filtersActive).toBe(true);
    });

    it("returns true when viewport filter active", () => {
      const store = useResultsStore();
      store.setRows([{ scenario_id: "s1" }]);
      store.viewport = "fhd";

      expect(store.filtersActive).toBe(true);
    });

    it("returns true when browser filter active", () => {
      const store = useResultsStore();
      store.setRows([{ scenario_id: "s1" }]);
      store.browser = "chromium";

      expect(store.filtersActive).toBe(true);
    });
  });

  describe("setRunId", () => {
    it("sets runId", () => {
      const store = useResultsStore();

      store.setRunId("run-123");

      expect(store.runId).toBe("run-123");
    });
  });

  describe("openViewer", () => {
    it("opens viewer with row and mode", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", status: "failed", actual_path: "a.png", diff_path: "d.png" },
      ]);
      store.setRunId("run-1");

      store.openViewer(store.rows[0], "test", 0);

      expect(store.modalOpen).toBe(true);
      expect(store.modalRow).toEqual(store.rows[0]);
      expect(store.viewerMode).toBe("test");
      expect(store.currentIndex).toBe(0);
    });

    it("sets tags from tagLog", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: { locked: true, synced: false, note: "test" } },
      };

      store.openViewer(store.rows[0], "test", 0);

      expect(store.currentTags.bug.locked).toBe(true);
      expect(store.currentTags.bug.note).toBe("test");
    });

    it("falls back to test mode for invalid modes", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png" },
      ]);

      store.openViewer(store.rows[0], "invalid", 0);

      expect(store.viewerMode).toBe("test");
    });
  });

  describe("closeViewer", () => {
    it("resets viewer state", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png" },
      ]);
      store.openViewer(store.rows[0], "test", 0);
      store.cursorX = 75;
      store.cursorY = 25;

      store.closeViewer();

      expect(store.modalOpen).toBe(false);
      expect(store.modalRow).toBeNull();
      expect(store.cursorX).toBe(50);
      expect(store.cursorY).toBe(50);
    });
  });

  describe("setColumns", () => {
    it("sets column count and updates slots", () => {
      const store = useResultsStore();

      store.setColumns(4);

      expect(store.columns).toBe(4);
      expect(store.slots).toHaveLength(4);
    });
  });

  describe("setSlotMode", () => {
    it("sets mode for specific slot", () => {
      const store = useResultsStore();
      store.setColumns(2);

      store.setSlotMode(1, "diff");

      expect(store.slots[0].mode).toBe("diff");
      expect(store.slotModes[1]).toBe("diff");
    });
  });

  describe("navigate", () => {
    it("navigates to next row", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png" },
        { scenario_id: "s2", actual_path: "b.png" },
      ]);
      store.openViewer(store.rows[0], "test", 0);

      store.navigate(1);

      expect(store.currentIndex).toBe(1);
      expect(store.modalRow.scenario_id).toBe("s2");
    });

    it("does not navigate beyond bounds", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png" },
      ]);
      store.openViewer(store.rows[0], "test", 0);

      store.navigate(1);

      expect(store.currentIndex).toBe(0);
    });
  });

  describe("navigateSelection", () => {
    it("navigates selection forward", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1" },
        { scenario_id: "s2" },
      ]);
      store.selectedIndex = 0;

      store.navigateSelection(1);

      expect(store.selectedIndex).toBe(1);
    });

    it("navigates selection backward", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1" },
        { scenario_id: "s2" },
      ]);
      store.selectedIndex = 1;

      store.navigateSelection(-1);

      expect(store.selectedIndex).toBe(0);
    });

    it("wraps to first when going below zero", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1" },
      ]);
      store.selectedIndex = 0;

      store.navigateSelection(-1);

      expect(store.selectedIndex).toBe(0);
    });

    it("wraps to last when going beyond length", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1" },
        { scenario_id: "s2" },
      ]);
      store.selectedIndex = 1;

      store.navigateSelection(1);

      expect(store.selectedIndex).toBe(1);
    });
  });

  describe("setCursorPosition", () => {
    it("sets cursor position based on mouse event", () => {
      const store = useResultsStore();
      const bounds = { left: 0, top: 0, width: 100, height: 100 };
      const evt = { clientX: 50, clientY: 50 };

      store.setCursorPosition(bounds, evt);

      expect(store.cursorX).toBe(50);
      expect(store.cursorY).toBe(50);
    });

    it("clamps values to 0-100", () => {
      const store = useResultsStore();
      const bounds = { left: 0, top: 0, width: 100, height: 100 };
      const evt = { clientX: -50, clientY: 150 };

      store.setCursorPosition(bounds, evt);

      expect(store.cursorX).toBe(0);
      expect(store.cursorY).toBe(100);
    });

    it("does nothing without bounds or evt", () => {
      const store = useResultsStore();

      store.setCursorPosition(null, {});
      expect(store.cursorX).toBe(50);

      store.setCursorPosition({}, null);
      expect(store.cursorY).toBe(50);
    });
  });

  describe("resetCursor", () => {
    it("resets cursor to center", () => {
      const store = useResultsStore();
      store.cursorX = 75;
      store.cursorY = 25;

      store.resetCursor();

      expect(store.cursorX).toBe(50);
      expect(store.cursorY).toBe(50);
    });
  });

  describe("selectRow", () => {
    it("sets selected index", () => {
      const store = useResultsStore();

      store.selectRow(5);

      expect(store.selectedIndex).toBe(5);
    });
  });

  describe("summary", () => {
    it("stores summary fields in state", () => {
      const store = useResultsStore();
      store.summary = { total: 10, passed: 5, failed: 3, skipped: 1, uncertain: 1 };

      expect(store.summary.total).toBe(10);
      expect(store.summary.passed).toBe(5);
      expect(store.summary.failed).toBe(3);
      expect(store.summary.skipped).toBe(1);
      expect(store.summary.uncertain).toBe(1);
    });
  });

  describe("gridStyle", () => {
    it("generates grid style for 2 columns", () => {
      const store = useResultsStore();
      store.columns = 2;

      const style = store.gridStyle;

      expect(style.gridTemplateColumns).toBe("repeat(2, minmax(0, 1fr))");
      expect(style.alignContent).toBe("start");
    });

    it("generates grid style for 4 columns", () => {
      const store = useResultsStore();
      store.columns = 4;

      const style = store.gridStyle;

      expect(style.gridTemplateColumns).toBe("repeat(2, minmax(0, 1fr))");
      expect(style.alignContent).toBe("center");
    });
  });

  describe("isTagReported", () => {
    it("returns true for synced bug", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.openViewer(store.rows[0], "test", 0);
      store.tagLog = {
        "s1::a.png::::": { bug: { locked: true, synced: true } },
      };

      expect(store.isTagReported("bug")).toBe(true);
    });

    it("returns false for unsynced bug", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.openViewer(store.rows[0], "test", 0);
      store.tagLog = {
        "s1::a.png::::": { bug: { locked: true, synced: false } },
      };

      expect(store.isTagReported("bug")).toBe(false);
    });

    it("returns true for synced aso", () => {
      const store = useResultsStore();
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.openViewer(store.rows[0], "test", 0);
      store.tagLog = {
        "s1::a.png::::": { aso: { locked: true, synced: true } },
      };

      expect(store.isTagReported("aso")).toBe(true);
    });

    it("returns false when no modal row", () => {
      const store = useResultsStore();
      store.modalRow = null;

      expect(store.isTagReported("bug")).toBe(false);
    });
  });

  describe("setOptimisticTag", () => {
    it("sets optimistic tag for case", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";

      store.setOptimisticTag(caseKey, "bug");

      expect(store.pendingTags[caseKey].bug).toBe(true);
    });


    it("clears existing sync error when setting optimistic tag", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";
      store.syncErrors[caseKey] = { message: "timeout", timestamp: Date.now() };

      store.setOptimisticTag(caseKey, "bug");

      expect(store.syncErrors[caseKey]).toBeUndefined();
    });

    it("does nothing with invalid inputs", () => {
      const store = useResultsStore();

      store.setOptimisticTag(null, "bug");
      store.setOptimisticTag("key", null);
      store.setOptimisticTag("", "bug");

      expect(store.pendingTags).toEqual({});
    });
  });

  describe("confirmTagSync", () => {
    it("removes pending tag after successful sync", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";
      store.pendingTags[caseKey] = { bug: true, aso: false };

      store.confirmTagSync(caseKey, "bug");

      expect(store.pendingTags[caseKey].bug).toBeUndefined();
    });

    it("clears sync error on confirm", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";
      store.pendingTags[caseKey] = { bug: true };
      store.syncErrors[caseKey] = { message: "timeout", timestamp: Date.now() };

      store.confirmTagSync(caseKey, "bug");

      expect(store.syncErrors[caseKey]).toBeUndefined();
    });

    it("removes case from pending when no tags left", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";
      store.pendingTags[caseKey] = { bug: true };

      store.confirmTagSync(caseKey, "bug");

      expect(store.pendingTags[caseKey]).toBeUndefined();
    });
  });

  describe("setSyncError", () => {
    it("sets sync error for case", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";

      store.setSyncError(caseKey, "timeout");

      expect(store.syncErrors[caseKey].message).toBe("timeout");
      expect(store.syncErrors[caseKey].timestamp).toBeDefined();
    });

    it("defaults error message to unknown", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";

      store.setSyncError(caseKey, null);

      expect(store.syncErrors[caseKey].message).toBe("unknown");
    });
  });

  describe("clearSyncError", () => {
    it("removes sync error for case", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";
      store.syncErrors[caseKey] = { message: "timeout", timestamp: Date.now() };

      store.clearSyncError(caseKey);

      expect(store.syncErrors[caseKey]).toBeUndefined();
    });
  });

  describe("hasPendingTag", () => {
    it("returns true when tag is pending", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";
      store.pendingTags[caseKey] = { bug: true };

      expect(store.hasPendingTag(caseKey, "bug")).toBe(true);
    });

    it("returns false when tag is not pending", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";
      store.pendingTags[caseKey] = { bug: true };

      expect(store.hasPendingTag(caseKey, "aso")).toBe(false);
    });

    it("returns false when case has no pending tags", () => {
      const store = useResultsStore();

      expect(store.hasPendingTag("s1::a.png::::", "bug")).toBe(false);
    });
  });

  describe("getSyncError", () => {
    it("returns sync error for case", () => {
      const store = useResultsStore();
      const caseKey = "s1::a.png::::";
      store.syncErrors[caseKey] = { message: "timeout", timestamp: 123 };

      const error = store.getSyncError(caseKey);

      expect(error.message).toBe("timeout");
    });

    it("returns null when no error", () => {
      const store = useResultsStore();

      expect(store.getSyncError("s1::a.png::::")).toBeNull();
    });
  });
});
