import { describe, expect, it, vi } from "vitest";

import ReportPage from "./ReportPage.vue";

function buildContext(overrides = {}) {
  const key = "scenario-1::actual.png::baseline.png::diff.png";
  return {
    prompt: { active: false, type: null },
    viewer: {
      modalRow: {
        scenario_id: "scenario-1",
        actual_path: "actual.png",
        baseline_path: "baseline.png",
        diff_path: "diff.png",
      },
      tagLog: {
        [key]: { bug: true, aso: false, baseline: false },
      },
      tags: { bug: true, aso: false, baseline: false },
      tagLocked: {
        [key]: { bug: true, aso: false, baseline: false },
      },
    },
    getRowTagKey: vi.fn(() => key),
    persistTags: vi.fn(),
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
