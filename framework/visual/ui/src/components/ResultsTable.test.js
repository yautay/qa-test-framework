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

  it("emits open-note when note badge is clicked", async () => {
    const row = makeRow({ actual_path: "actual-note.png" });
    const key = rowKey(row);
    const wrapper = mount(ResultsTable, {
      props: {
        rows: [row],
        fmt: (value) => String(value ?? ""),
        tagLog: {
          [key]: {
            note: {
              text: "Keep this result",
            },
          },
        },
        tagKeyForRow: rowKey,
        selectedIndex: -1,
      },
    });

    await wrapper.get(".note-badge").trigger("click");

    const emitted = wrapper.emitted("open-note");
    expect(emitted).toBeTruthy();
    expect(emitted[0][0]).toEqual(row);
    expect(emitted[0][1]).toBe(0);
  });
});
