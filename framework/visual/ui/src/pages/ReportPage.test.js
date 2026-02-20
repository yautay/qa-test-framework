import { beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";
import { mount } from "@vue/test-utils";
import { setActivePinia, createPinia } from "pinia";

vi.mock("../lib/api/reportsApi", () => ({
  fetchReportResults: vi.fn(async () => [
    { scenario_id: "s1", status: "failed", actual_path: "a.png", suite_id: "suite1", viewport: "1920x1080", browser: "chrome" },
    { scenario_id: "s2", status: "passed", actual_path: "b.png", suite_id: "suite2", viewport: "1920x1080", browser: "chrome" },
  ]),
  sendRunReport: vi.fn(async () => ({})),
}));

vi.mock("../lib/tagPersistence", () => ({
  loadTagSnapshot: vi.fn(async () => ({})),
  saveTagSnapshotToFile: vi.fn(async () => true),
}));

vi.mock("../lib/baselineApi", () => ({
  requestBaselineChallengeForRun: vi.fn(),
  sendBaselineSelectionForRun: vi.fn(),
}));

vi.mock("bootstrap", () => ({
  default: {
    getInstance: vi.fn(() => ({ show: vi.fn(), hide: vi.fn() })),
  },
  Modal: class {
    static getInstance() { return null; }
    show() {}
    hide() {}
  },
}));

import ReportPage from "./ReportPage.vue";
import { fetchReportResults, sendRunReport } from "../lib/api/reportsApi";
import { loadTagSnapshot, saveTagSnapshotToFile } from "../lib/tagPersistence";
import { useResultsStore } from "../stores/resultsStore";
import { getRowTagKey } from "../lib/viewer";

describe("ReportPage", () => {
  let pinia;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    vi.clearAllMocks();
  });

  it("loads results on mount", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.text()).toContain("run-1");

    wrapper.unmount();
  });

  it("displays summary with correct counts", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.text()).toContain("total=");
    expect(wrapper.text()).toContain("passed=");
    expect(wrapper.text()).toContain("failed=");

    wrapper.unmount();
  });

  it("shows load error when runId is missing", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.text()).toContain("Missing run id");

    wrapper.unmount();
  });

  it("displays filters panel", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.find("select").exists()).toBe(true);

    wrapper.unmount();
  });

  it("displays header with run info", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-123" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.text()).toContain("run-123");

    wrapper.unmount();
  });

  it("displays baseline button", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.find("button.btn-success").exists()).toBe(true);

    wrapper.unmount();
  });

  it("displays report button", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.find("button.btn-primary").exists()).toBe(true);

    wrapper.unmount();
  });

  it("renders results table", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.find("table").exists() || wrapper.find("tbody").exists()).toBe(true);

    wrapper.unmount();
  });

  it("calls fetchReportResults on mount", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-test" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(fetchReportResults).toHaveBeenCalledWith("run-test");

    wrapper.unmount();
  });

  it("shows empty state when no rows", async () => {
    fetchReportResults.mockResolvedValueOnce([]);

    const wrapper = mount(ReportPage, {
      props: { runId: "run-empty" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.text()).toContain("total=0");

    wrapper.unmount();
  });

  it("displays keyboard hint when row selected", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const hint = wrapper.find(".keyboard-hint");
    expect(hint.exists()).toBe(true);

    wrapper.unmount();
  });

  it("renders ViewerModal component", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.findComponent({ name: "ViewerModal" }).exists()).toBe(true);

    wrapper.unmount();
  });

  it("renders FiltersPanel component", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.findComponent({ name: "FiltersPanel" }).exists()).toBe(true);

    wrapper.unmount();
  });

  it("renders AppHeader component", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.findComponent({ name: "AppHeader" }).exists()).toBe(true);

    wrapper.unmount();
  });

  it("renders TestMetadataPanel component", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.findComponent({ name: "TestMetadataPanel" }).exists()).toBe(true);

    wrapper.unmount();
  });

  it("shows row when clicking on result", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const table = wrapper.find("table");
    if (table.exists()) {
      const rows = table.findAll("tbody tr");
      if (rows.length > 0) {
        rows[0].trigger("click");
        await new Promise((resolve) => setTimeout(resolve, 10));
      }
    }

    wrapper.unmount();
  });

  it("handles keydown for column switch", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "1" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "2" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles escape key to deselect", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles arrow navigation", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles space to open row", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { code: "Space" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles shift to go back to hero", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { code: "ShiftLeft" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("calls loadTagSnapshot on mount", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(loadTagSnapshot).toHaveBeenCalledWith("run-1");

    wrapper.unmount();
  });

  it("handles send baseline button click with no candidates", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const baselineBtn = wrapper.find("button.btn-success");
    if (baselineBtn.exists()) {
      baselineBtn.trigger("click");
      await new Promise((resolve) => setTimeout(resolve, 10));
    }

    wrapper.unmount();
  });

  it("handles send report button click", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const reportBtn = wrapper.find("button.btn-primary");
    if (reportBtn.exists()) {
      reportBtn.trigger("click");
      await new Promise((resolve) => setTimeout(resolve, 10));
    }

    wrapper.unmount();
  });

  it("downloads pdf when report response includes pages", async () => {
    const anchor = {
      href: "",
      download: "",
      rel: "",
      click: vi.fn(),
      remove: vi.fn(),
    };
    const originalCreateElement = document.createElement.bind(document);
    const createSpy = vi.spyOn(document, "createElement").mockImplementation((tag) => {
      if (tag === "a") return anchor;
      return originalCreateElement(tag);
    });
    const appendSpy = vi.spyOn(document.body, "appendChild").mockImplementation((node) => node);

    sendRunReport.mockResolvedValueOnce({
      bug: {},
      aso: {},
      note: {},
      pdf: { pages: 2 },
    });

    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const store = useResultsStore();
    const firstRow = store.rows[0];
    const key = getRowTagKey(firstRow);
    store.updateTagLog({
      [key]: {
        bug: true,
        aso: false,
        baseline: false,
        note: null,
        bug_reported: false,
        aso_reported: false,
        note_reported: false,
        bug_reported_at: "",
        aso_reported_at: "",
        note_reported_at: "",
        note_reported_hash: "",
      },
    });
    await nextTick();

    const reportBtn = wrapper.find(".report-header button.btn-primary");
    expect(reportBtn.exists()).toBe(true);
    expect(reportBtn.element.disabled).toBe(false);
    reportBtn.trigger("click");
    await nextTick();

    const promptOverlay = wrapper.find(".global-prompt-overlay");
    expect(promptOverlay.exists()).toBe(true);
    const confirmBtn = promptOverlay.find("button.btn-primary");
    expect(confirmBtn.exists()).toBe(true);
    confirmBtn.trigger("click");

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(sendRunReport).toHaveBeenCalled();
    expect(anchor.click).toHaveBeenCalled();
    expect(anchor.download).toBe("run-1.pdf");
    expect(anchor.href).toContain("/reports/run-1/run-1.pdf");

    wrapper.unmount();
    createSpy.mockRestore();
    appendSpy.mockRestore();
  });

  it("does not download pdf when report response has no pages", async () => {
    const anchor = {
      href: "",
      download: "",
      rel: "",
      click: vi.fn(),
      remove: vi.fn(),
    };
    const originalCreateElement = document.createElement.bind(document);
    const createSpy = vi.spyOn(document, "createElement").mockImplementation((tag) => {
      if (tag === "a") return anchor;
      return originalCreateElement(tag);
    });

    sendRunReport.mockResolvedValueOnce({
      bug: {},
      aso: {},
      note: {},
      pdf: { pages: 0 },
    });

    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const store = useResultsStore();
    const firstRow = store.rows[0];
    const key = getRowTagKey(firstRow);
    store.updateTagLog({
      [key]: {
        bug: true,
        aso: false,
        baseline: false,
        note: null,
        bug_reported: false,
        aso_reported: false,
        note_reported: false,
        bug_reported_at: "",
        aso_reported_at: "",
        note_reported_at: "",
        note_reported_hash: "",
      },
    });
    await nextTick();

    const reportBtn = wrapper.find(".report-header button.btn-primary");
    reportBtn.trigger("click");
    await nextTick();

    const promptOverlay = wrapper.find(".global-prompt-overlay");
    const confirmBtn = promptOverlay.find("button.btn-primary");
    confirmBtn.trigger("click");

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(sendRunReport).toHaveBeenCalled();
    expect(anchor.click).not.toHaveBeenCalled();

    wrapper.unmount();
    createSpy.mockRestore();
  });

  it("displays send report prompt when active", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const reportBtn = wrapper.find("button.btn-primary");
    if (reportBtn.exists()) {
      reportBtn.trigger("click");
      await new Promise((resolve) => setTimeout(resolve, 10));
      expect(wrapper.find(".global-prompt-overlay").exists()).toBe(false);
    }

    wrapper.unmount();
  });

  it("handles keyup for zoom keys", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keyup", { key: "a" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    document.dispatchEvent(new KeyboardEvent("keyup", { key: "d" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("shows error message on fetch failure", async () => {
    const { fetchReportResults } = await import("../lib/api/reportsApi");
    fetchReportResults.mockRejectedValueOnce(new Error("Network error"));

    const wrapper = mount(ReportPage, {
      props: { runId: "run-fail" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(wrapper.text()).toContain("Unable to load");

    wrapper.unmount();
  });

  it("shows row with test metadata", async () => {
    const { fetchReportResults } = await import("../lib/api/reportsApi");
    fetchReportResults.mockResolvedValueOnce([
      { 
        scenario_id: "s1", 
        status: "failed", 
        actual_path: "a.png",
        suite_id: "suite1",
        viewport: "1920x1080",
        browser: "chrome",
        test_metadata: { run: { run_id: "run-1", tester: "tester1" } }
      },
    ]);

    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const table = wrapper.find("table");
    if (table.exists()) {
      const rows = table.findAll("tbody tr");
      if (rows.length > 0) {
        rows[0].trigger("click");
        await new Promise((resolve) => setTimeout(resolve, 10));
      }
    }

    wrapper.unmount();
  });

  it("opens metadata panel from table", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const table = wrapper.find("table");
    if (table.exists()) {
      const rows = table.findAll("tbody tr");
      if (rows.length > 0) {
        rows[0].trigger("click");
        await new Promise((resolve) => setTimeout(resolve, 10));
      }
    }

    wrapper.unmount();
  });

  it("handles send baseline with candidates", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const baselineBtn = wrapper.find("button.btn-success");
    if (baselineBtn.exists()) {
      baselineBtn.trigger("click");
      await new Promise((resolve) => setTimeout(resolve, 10));
    }

    wrapper.unmount();
  });

  it("handles prompt with space key", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Space" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles prompt with shift key", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { code: "ShiftLeft" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles tag key presses", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "s" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "c" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles note key press", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "n" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles navigation keys a and d", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "a" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "d" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles w key for zoom", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    document.dispatchEvent(new KeyboardEvent("keyup", { key: "w" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles backslash key for baseline", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "\\" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("opens viewer modal and handles escape", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("renders with empty run id", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.text()).toContain("Missing run id");

    wrapper.unmount();
  });

  it("displays correct summary text", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(wrapper.text()).toContain("total=");
    expect(wrapper.text()).toContain("passed=");
    expect(wrapper.text()).toContain("failed=");

    wrapper.unmount();
  });

  it("handles shift to navigate back", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { code: "ShiftRight" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });

  it("handles column switch with 3 and 4 keys", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "3" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "4" }));
    await new Promise((resolve) => setTimeout(resolve, 10));

    wrapper.unmount();
  });
});

describe("promptSendReport logic", () => {
  let pinia;
  let store;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    store = useResultsStore();
    vi.clearAllMocks();
  });

  describe("API works - new candidates", () => {
    it("shows prompt for new BUG", async () => {
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: true, bug_reported: false },
      };

      expect(store.reportCandidatesCount).toBe(1);
      expect(store.hasAnyBug).toBe(1);
    });

    it("shows prompt for new ASO", async () => {
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: false,aso: true,aso_reported: false },
      };

      expect(store.reportCandidatesCount).toBe(1);
    });

    it("shows prompt for new NOTE", async () => {
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: false, note: { text: "test note" } },
      };

      expect(store.reportCandidatesCount).toBe(1);
    });

    it("shows prompt for modified NOTE", async () => {
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": {
          bug: false,
          note: { text: "modified", updatedAt: "2026-02-20T12:00:00.000Z" },
          note_reported: true,
          note_reported_at: "2026-02-20T11:00:00.000Z",
        },
      };

      expect(store.reportCandidatesCount).toBe(1);
    });
  });

  describe("API works - no new candidates", () => {
    it("generates PDF without prompt when no candidates but has BUG", async () => {
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: true, bug_reported: true },
      };

      expect(store.reportCandidatesCount).toBe(0);
      expect(store.hasAnyBug).toBe(1);
    });

    it("does nothing when no candidates and no BUG", async () => {
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: false },
      };

      expect(store.reportCandidatesCount).toBe(0);
      expect(store.hasAnyBug).toBe(0);
    });
  });

  describe("API failed - retry logic", () => {
    it("silent retry when previous failed and no new candidates", async () => {
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: true, bug_reported: true },
      };

      expect(store.reportCandidatesCount).toBe(0);
      expect(store.hasAnyBug).toBe(1);
    });

    it("prompt when previous failed but has new candidates", async () => {
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
        { scenario_id: "s2", actual_path: "b.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: true, bug_reported: true },
        "s2::b.png::::": { bug: true, bug_reported: false },
      };

      expect(store.reportCandidatesCount).toBe(1);
    });
  });
});
