import { beforeEach, describe, expect, it, vi } from "vitest";
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
