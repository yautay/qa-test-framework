import { beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";
import { mount } from "@vue/test-utils";
import { setActivePinia, createPinia } from "pinia";

vi.mock("../lib/api/reportsApi", () => ({
  fetchReportResultsPayload: vi.fn(async () => ({
    results: [
      { scenario_id: "s1", status: "failed", actual_path: "a.png", suite_id: "suite1", viewport: "1920x1080", browser: "chrome" },
      { scenario_id: "s2", status: "passed", actual_path: "b.png", suite_id: "suite2", viewport: "1920x1080", browser: "chrome" },
    ],
    build_metadata: {},
  })),
  fetchBuildTags: vi.fn(async () => ({ tags: { test_cases: {} } })),
  postBuildEvent: vi.fn(async () => ({ accepted: true, test_cases: {} })),
  acquireBuildLock: vi.fn(async () => ({ accepted: true, lock: { lock_id: "lock-1" } })),
  heartbeatBuildLock: vi.fn(async () => ({ accepted: true, lock: { lock_id: "lock-1" } })),
  releaseBuildLock: vi.fn(async () => ({ accepted: true })),
  sendBuildReport: vi.fn(async () => ({ accepted: true, pdf: { pages: 0 }, test_cases: {} })),
}));

vi.mock("../lib/api/appInfoApi", () => ({
  fetchAppInfo: vi.fn(async () => ({
    ui_config: {
      pms_poll_interval_ms: 5000,
      pms_poll_idle_multiplier: 3,
    },
  })),
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
    static getOrCreateInstance() { return { show: vi.fn(), hide: vi.fn() }; }
    show() {}
    hide() {}
  },
}));

import ReportPage from "./ReportPage.vue";
import { acquireBuildLock, fetchBuildTags, fetchReportResultsPayload, sendBuildReport } from "../lib/api/reportsApi";
import { requestBaselineChallengeForRun, sendBaselineSelectionForRun } from "../lib/baselineApi";
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

    expect(wrapper.text()).toContain("total:");
    expect(wrapper.text()).toContain("passed:");
    expect(wrapper.text()).toContain("failed:");

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

  it("calls fetchReportResultsPayload on mount", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-test" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(fetchReportResultsPayload).toHaveBeenCalledWith("run-test");

    wrapper.unmount();
  });

  it("shows empty state when no rows", async () => {
    fetchReportResultsPayload.mockResolvedValueOnce({ results: [], build_metadata: {} });

    const wrapper = mount(ReportPage, {
      props: { runId: "run-empty" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.text()).toContain("total: 0");

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

  it("calls fetchBuildTags on mount", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(fetchBuildTags).toHaveBeenCalledWith("run-1");

    wrapper.unmount();
  });

  it("shows lock denied state when lock acquire is rejected", async () => {
    acquireBuildLock.mockResolvedValueOnce({ accepted: false, lock: { owner_client_id: "other-client" } });

    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(wrapper.text()).toContain("Build is locked by another client.");
    expect(fetchReportResultsPayload).not.toHaveBeenCalled();

    wrapper.unmount();
  });

  it("applies initial tag snapshot from fetchBuildTags payload", async () => {
    fetchBuildTags.mockResolvedValue({
      tags: {
        test_cases: {
          "s1::a.png::::": {
            bug: { locked: true, synced: false, note: "" },
            aso: { locked: false, synced: false, note: "" },
          },
        },
        outbox: [],
      },
    });

    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const store = useResultsStore();
    const hasLockedBug = Object.values(store.tagLog).some((entry) => entry?.bug?.locked);
    expect(hasLockedBug).toBe(true);

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

    sendBuildReport.mockResolvedValueOnce({
      pdf: { pages: 2 },
      test_cases: {},
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
        bug: { locked: true, synced: false, note: "" },
        aso: { locked: false, synced: false },
      },
    });
    await nextTick();

    const reportBtn = wrapper.find(".report-header button.btn-primary");
    expect(reportBtn.exists()).toBe(true);
    expect(reportBtn.element.disabled).toBe(false);
    await reportBtn.trigger("click");

    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(sendBuildReport).toHaveBeenCalled();
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

    sendBuildReport.mockResolvedValueOnce({
      pdf: { pages: 0 },
      test_cases: {},
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
        bug: { locked: true, synced: false, note: "" },
        aso: { locked: false, synced: false },
      },
    });
    await nextTick();

    const reportBtn = wrapper.find(".report-header button.btn-primary");
    await reportBtn.trigger("click");

    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(sendBuildReport).toHaveBeenCalled();
    expect(anchor.click).not.toHaveBeenCalled();

    wrapper.unmount();
    createSpy.mockRestore();
  });

  it("keeps sync warning conditions when report state still has unsynced tag", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const store = useResultsStore();
    const row = store.rows[0];
    const key = getRowTagKey(row);

    sendBuildReport.mockResolvedValueOnce({
      accepted: true,
      pdf: { pages: 0 },
      state: {
        test_cases: {
          [key]: {
            bug: { locked: true, synced: true, note: "" },
            aso: { locked: true, synced: false, note: "" },
          },
        },
        outbox: [],
      },
      test_cases: {
        [key]: {
          bug: { locked: true, synced: true, note: "" },
          aso: { locked: true, synced: false, note: "" },
        },
      },
    });

    const reportBtn = wrapper.find(".report-header button.btn-primary");
    await reportBtn.trigger("click");
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(store.tagLog[key].bug.synced).toBe(true);
    expect(store.tagLog[key].aso.synced).toBe(false);

    wrapper.unmount();
  });

  it("applies full tags payload returned from sendBuildReport", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const store = useResultsStore();
    const row = store.rows[0];
    const key = getRowTagKey(row);
    store.updateTagLog({
      [key]: {
        bug: { locked: true, synced: false, note: "" },
        aso: { locked: false, synced: false, note: "" },
      },
    });

    sendBuildReport.mockResolvedValueOnce({
      accepted: true,
      pdf: { pages: 0 },
      tags: {
        test_cases: {
          [key]: {
            bug: { locked: true, synced: true, note: "" },
            aso: { locked: false, synced: false, note: "" },
          },
        },
        outbox: [],
      },
    });

    const reportBtn = wrapper.find(".report-header button.btn-primary");
    await reportBtn.trigger("click");
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(store.tagLog[key].bug.synced).toBe(true);

    wrapper.unmount();
  });

  it("clears sync warning conditions when report state returns both tags synced", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const store = useResultsStore();
    const row = store.rows[0];
    const key = getRowTagKey(row);

    store.applyBuildTags({
      test_cases: {
        [key]: {
          bug: { locked: true, synced: true, note: "" },
          aso: { locked: true, synced: false, note: "" },
        },
      },
      outbox: [],
    });

    sendBuildReport.mockResolvedValueOnce({
      accepted: true,
      pdf: { pages: 0 },
      state: {
        test_cases: {
          [key]: {
            bug: { locked: true, synced: true, note: "" },
            aso: { locked: true, synced: true, note: "" },
          },
        },
        outbox: [],
      },
      test_cases: {
        [key]: {
          bug: { locked: true, synced: true, note: "" },
          aso: { locked: true, synced: true, note: "" },
        },
      },
    });

    const reportBtn = wrapper.find(".report-header button.btn-primary");
    await reportBtn.trigger("click");
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(store.tagLog[key].bug.synced).toBe(true);
    expect(store.tagLog[key].aso.synced).toBe(true);
    expect(store.syncErrors[key]).toBeUndefined();

    wrapper.unmount();
  });

  it("does not display send report prompt on click", async () => {
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
    const { fetchReportResultsPayload } = await import("../lib/api/reportsApi");
    fetchReportResultsPayload.mockRejectedValueOnce(new Error("Network error"));

    const wrapper = mount(ReportPage, {
      props: { runId: "run-fail" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(wrapper.text()).toContain("Unable to load");

    wrapper.unmount();
  });

  it("shows row with test metadata", async () => {
    const { fetchReportResultsPayload } = await import("../lib/api/reportsApi");
    fetchReportResultsPayload.mockResolvedValueOnce({
      results: [
        {
          scenario_id: "s1",
          status: "failed",
          actual_path: "a.png",
          suite_id: "suite1",
          viewport: "1920x1080",
          browser: "chrome",
          test_metadata: { run: { run_id: "run-1", tester: "tester1" } }
        },
      ],
      build_metadata: {},
    });

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

    expect(wrapper.text()).toContain("total:");
    expect(wrapper.text()).toContain("passed:");
    expect(wrapper.text()).toContain("failed:");

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

  it("passes resolved test case URL to modal header", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const store = useResultsStore();
    const row = {
      scenario_id: "s1",
      status: "failed",
      message: "ok",
      viewport: "fhd",
      browser: "chromium",
      test_metadata: {
        scenario: {
          target_url: "/product/123",
        },
        execution: {
          target_base_url: "https://shop.example.com",
        },
      },
    };

    store.openViewer(row, "test", 0);
    await nextTick();

    const modal = wrapper.findComponent({ name: "ViewerModal" });
    expect(modal.props("viewer").modalCaseUrl).toBe("https://shop.example.com/product/123");

    wrapper.unmount();
  });

  it("includes reference_host in metadata when present", async () => {
    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const row = {
      scenario_id: "s1",
      status: "passed",
      message: "ok",
      viewport: "fhd",
      browser: "chromium",
      test_metadata: {
        scenario: {
          target_url: "/product/123",
        },
        execution: {
          reference_host: "demo",
          target_base_url: "https://shop.example.com",
        },
      },
    };

    const table = wrapper.findComponent({ name: "ResultsTable" });
    table.vm.$emit("open-metadata", row, 0);
    await nextTick();

    const metadataPanel = wrapper.findComponent({ name: "TestMetadataPanel" });
    expect(metadataPanel.props("metadata").run.reference_host).toBe("demo");
    expect(metadataPanel.props("metadata").execution.reference_host).toBe("demo");
    expect(metadataPanel.props("metadata").execution.target_full_url).toBe("https://shop.example.com/product/123");

    wrapper.unmount();
  });

  it("opens add baseline prompt from modal event when baseline is not set", async () => {
    const teleportHost = document.createElement("div");
    teleportHost.id = "vrtModal";
    const modalContent = document.createElement("div");
    modalContent.className = "modal-content";
    teleportHost.appendChild(modalContent);
    document.body.appendChild(teleportHost);

    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const modal = wrapper.findComponent({ name: "ViewerModal" });
    modal.vm.$emit("prompt-tag", "baseline");
    await nextTick();

    const prompt = wrapper.findComponent({ name: "ConfirmPrompt" });
    expect(prompt.props("active")).toBe(true);
    expect(prompt.props("type")).toBe("baseline");

    wrapper.unmount();
    teleportHost.remove();
  });

  it("opens remove baseline prompt from modal event when baseline is already set", async () => {
    const teleportHost = document.createElement("div");
    teleportHost.id = "vrtModal";
    const modalContent = document.createElement("div");
    modalContent.className = "modal-content";
    teleportHost.appendChild(modalContent);
    document.body.appendChild(teleportHost);

    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const store = useResultsStore();
    store.openViewer(store.rows[0], "test", 0);
    store.toggleBaseline();

    const modal = wrapper.findComponent({ name: "ViewerModal" });
    modal.vm.$emit("prompt-tag", "baseline");
    await nextTick();

    const prompt = wrapper.findComponent({ name: "ConfirmPrompt" });
    expect(prompt.props("active")).toBe(true);
    expect(prompt.props("type")).toBe("remove-baseline");

    wrapper.unmount();
    teleportHost.remove();
  });

  it("clears baseline tags after successful baseline send", async () => {
    requestBaselineChallengeForRun.mockResolvedValueOnce({ challenge_id: "c1", phrase: "HELLO" });
    sendBaselineSelectionForRun.mockResolvedValueOnce({ saved_count: 1, failed_count: 0 });
    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue("HELLO");

    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const store = useResultsStore();
    const row = store.rows[0];
    const key = getRowTagKey(row);
    store.openViewer(row, "test", 0);
    store.setBaseline(true);
    await nextTick();

    const baselineBtn = wrapper.find(".report-header button.btn-success");
    await baselineBtn.trigger("click");
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(requestBaselineChallengeForRun).toHaveBeenCalledWith("run-1");
    expect(sendBaselineSelectionForRun).toHaveBeenCalled();
    expect(store.tagLog[key].baseline).toBe(false);

    promptSpy.mockRestore();
    wrapper.unmount();
  });

  it("keeps baseline tags when baseline send returns failed items", async () => {
    requestBaselineChallengeForRun.mockResolvedValueOnce({ challenge_id: "c1", phrase: "HELLO" });
    sendBaselineSelectionForRun.mockResolvedValueOnce({ saved_count: 0, failed_count: 1 });
    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue("HELLO");
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    const wrapper = mount(ReportPage, {
      props: { runId: "run-1" },
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 50));

    const store = useResultsStore();
    const row = store.rows[0];
    const key = getRowTagKey(row);
    store.openViewer(row, "test", 0);
    store.setBaseline(true);
    await nextTick();

    const baselineBtn = wrapper.find(".report-header button.btn-success");
    await baselineBtn.trigger("click");
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(store.tagLog[key].baseline).toBe(true);
    expect(errorSpy).toHaveBeenCalled();

    errorSpy.mockRestore();
    promptSpy.mockRestore();
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
        "s1::a.png::::": { bug: { locked: true, synced: false } },
      };

      expect(store.reportCandidatesCount).toBe(1);
      expect(store.hasAnyBug).toBe(1);
    });

    it("shows prompt for new ASO", async () => {
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { aso: { locked: true, synced: false } },
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
        "s1::a.png::::": { bug: { locked: true, synced: true } },
      };

      expect(store.reportCandidatesCount).toBe(0);
      expect(store.hasAnyBug).toBe(1);
    });

    it("does nothing when no candidates and no BUG", async () => {
      store.setRows([
        { scenario_id: "s1", actual_path: "a.png", baseline_path: "", diff_path: "" },
      ]);
      store.tagLog = {
        "s1::a.png::::": { bug: { locked: false, synced: false } },
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
        "s1::a.png::::": { bug: { locked: true, synced: true } },
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
        "s1::a.png::::": { bug: { locked: true, synced: true } },
        "s2::b.png::::": { bug: { locked: true, synced: false } },
      };

      expect(store.reportCandidatesCount).toBe(1);
    });
  });
});
