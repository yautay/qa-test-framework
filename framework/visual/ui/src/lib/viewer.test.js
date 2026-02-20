import { describe, expect, it } from "vitest";

import { createViewerState, getModeSrc, openViewer } from "./viewer";

function buildRow(overrides = {}) {
  return {
    scenario_id: "scenario-1",
    status: "failed",
    compare_mode: "pixel",
    suite_id: "suite-a",
    viewport: "fhd",
    browser: "chromium",
    actual_path: "actual/image.png",
    diff_path: "diff/image.png",
    heatmap_path: "heatmap/image.png",
    ...overrides,
  };
}

describe("viewer", () => {
  it("builds ref image source from API endpoint", () => {
    const viewer = createViewerState();
    const row = buildRow();

    openViewer(viewer, row, "ref", 0, { runId: "20260218_120000_000001" });

    expect(viewer.modalRefSrc).toBe(
      "/api/reports/20260218_120000_000001/image/ref?suite_id=suite-a&scenario_id=scenario-1&viewport=fhd&browser=chromium"
    );
    expect(getModeSrc(viewer, "ref")).toBe(viewer.modalRefSrc);
  });

  it("prefixes report assets for test/diff/lpips with run route", () => {
    const viewer = createViewerState();
    const row = buildRow();

    openViewer(viewer, row, "test", 0, { runId: "run-1" });

    expect(viewer.modalTestSrc).toBe("/reports/run-1/actual/image.png");
    expect(viewer.modalDiffSrc).toBe("/reports/run-1/diff/image.png");
    expect(viewer.modalLpipsSrc).toBe("/reports/run-1/heatmap/image.png");
  });

  it("falls back to test mode when ref metadata is incomplete", () => {
    const viewer = createViewerState();
    const row = buildRow({ suite_id: "" });

    openViewer(viewer, row, "ref", 0, { runId: "run-2" });

    expect(viewer.modalRefSrc).toBe("");
    expect(viewer.viewerMode).toBe("test");
    expect(viewer.modalImgSrc).toBe("/reports/run-2/actual/image.png");
  });

  it("keeps absolute test path unchanged", () => {
    const viewer = createViewerState();
    const row = buildRow({ actual_path: "https://example.test/img.png" });

    openViewer(viewer, row, "test", 0, { runId: "run-3" });

    expect(viewer.modalTestSrc).toBe("https://example.test/img.png");
  });
});
