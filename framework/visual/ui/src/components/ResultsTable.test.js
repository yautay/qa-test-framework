import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";

import ResultsTable from "./ResultsTable.vue";

vi.mock("../lib/i18n", () => ({
  t: (key) => key,
}));

function makeRow(overrides = {}) {
  return {
    scenario_id: "full_page",
    status: "failed",
    compare_mode: "pixel",
    pixel_changed_ratio: 0.1,
    lpips: 0.2,
    dists: 0.3,
    message: "row",
    baseline_path: "baseline.png",
    actual_path: "actual.png",
    diff_path: "diff.png",
    ...overrides,
  };
}

function rowKey(row) {
  return [
    row?.scenario_id || "",
    row?.actual_path || "",
    row?.baseline_path || "",
    row?.diff_path || "",
  ].join("::");
}

describe("ResultsTable", () => {
  it("renders columns in expected order with metadata at end", () => {
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [makeRow()],
        fmt: (value) => String(value ?? ""),
        tagLog: {},
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    const headers = wrapper.findAll("thead th").map((cell) => cell.text());
    expect(headers).toEqual([
      "listing.scenario",
      "listing.browser",
      "listing.viewport",
      "listing.signals",
      "listing.status",
      "listing.pixel",
      "listing.lpips",
      "listing.dists",
      "listing.message",
      "listing.artifacts",
      "listing.metadata",
    ]);
  });

  it("updates rendered row correctly when duplicate scenario ids exist", async () => {
    const passedRow = makeRow({ status: "passed", actual_path: "actual-pass.png", diff_path: "diff-pass.png" });
    const failedRow = makeRow({ status: "failed", actual_path: "actual-fail.png", diff_path: "diff-fail.png" });

    const wrapper = mount(ResultsTable, {
      props: {
        rows: [passedRow, failedRow],
        fmt: (value) => String(value ?? ""),
        tagLog: {},
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    await wrapper.setProps({ rows: [failedRow] });

    const rows = wrapper.findAll("tbody tr");
    expect(rows).toHaveLength(1);
    expect(rows[0].text()).toContain("failed");
    expect(rows[0].text()).not.toContain("passed");
  });

  it("emits open-metadata when metadata icon is clicked", async () => {
    const row = makeRow({ actual_path: "actual-meta.png" });
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [row],
        fmt: (value) => String(value ?? ""),
        tagLog: {},
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    await wrapper.get(".metadata-icon").trigger("click");

    const emitted = wrapper.emitted("open-metadata");
    expect(emitted).toBeTruthy();
    expect(emitted[0][0]).toEqual(row);
    expect(emitted[0][1]).toBe(0);
  });

  it("shows sync warning when one tag remains unsynced", () => {
    const row = makeRow();
    const key = rowKey(row);
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [row],
        fmt: (value) => String(value ?? ""),
        tagLog: {
          [key]: {
            bug: { locked: true, synced: true },
            aso: { locked: true, synced: false },
            baseline: false,
          },
        },
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    const warning = wrapper.find(".sync-error-icon");
    expect(warning.exists()).toBe(true);
    expect(warning.attributes("title")).toBe("sync.unsyncedTooltip");
  });

  it("shows localized error tooltip when sync error exists", () => {
    const row = makeRow();
    const key = rowKey(row);
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [row],
        fmt: (value) => String(value ?? ""),
        tagLog: {},
        syncErrors: {
          [key]: { message: "timeout" },
        },
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    const warning = wrapper.find(".sync-error-icon");
    expect(warning.exists()).toBe(true);
    expect(warning.attributes("title")).toBe("sync.errorPrefix: timeout");
  });

  it("prefers error tooltip over pending and unsynced states", () => {
    const row = makeRow();
    const key = rowKey(row);
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [row],
        fmt: (value) => String(value ?? ""),
        tagLog: {
          [key]: {
            bug: { locked: true, synced: false },
            aso: { locked: false, synced: false },
            baseline: false,
          },
        },
        pendingTags: {
          [key]: { bug: true },
        },
        syncErrors: {
          [key]: { message: "conflict" },
        },
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    const warning = wrapper.find(".sync-error-icon");
    expect(warning.exists()).toBe(true);
    expect(warning.attributes("title")).toBe("sync.errorPrefix: conflict");
  });

  it("shows pending tooltip when no sync error exists", () => {
    const row = makeRow();
    const key = rowKey(row);
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [row],
        fmt: (value) => String(value ?? ""),
        tagLog: {
          [key]: {
            bug: { locked: true, synced: false },
            aso: { locked: false, synced: false },
            baseline: false,
          },
        },
        pendingTags: {
          [key]: { bug: true },
        },
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    const warning = wrapper.find(".sync-error-icon");
    expect(warning.exists()).toBe(true);
    expect(warning.attributes("title")).toBe("sync.pendingTooltip");
  });

  it("hides sync warning when BUG and ASO are fully synced", () => {
    const row = makeRow();
    const key = rowKey(row);
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [row],
        fmt: (value) => String(value ?? ""),
        tagLog: {
          [key]: {
            bug: { locked: true, synced: true },
            aso: { locked: true, synced: true },
            baseline: false,
          },
        },
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    expect(wrapper.find(".sync-error-icon").exists()).toBe(false);
  });

  it("shows PMS pending icon for queued/running test", () => {
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [makeRow({ perceptual: { status: "queued" } })],
        fmt: (value) => String(value ?? ""),
        tagLog: {},
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    const icon = wrapper.find(".pms-pending-icon");
    expect(icon.exists()).toBe(true);
    expect(icon.attributes("title")).toBe("pms.pendingTest");
  });

  it("shows PMS error icon with detailed tooltip", () => {
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [makeRow({ perceptual: { status: "error", error_message: "gpu oom" } })],
        fmt: (value) => String(value ?? ""),
        tagLog: {},
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    const icon = wrapper.find(".pms-error-icon");
    expect(icon.exists()).toBe(true);
    expect(icon.attributes("title")).toBe("pms.errorTest: gpu oom");
  });

  it("shows PMS success icon for done test", () => {
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [makeRow({ perceptual: { status: "done" } })],
        fmt: (value) => String(value ?? ""),
        tagLog: {},
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    const icon = wrapper.find(".pms-success-icon");
    expect(icon.exists()).toBe(true);
    expect(icon.attributes("title")).toBe("pms.successTest");
  });
});
