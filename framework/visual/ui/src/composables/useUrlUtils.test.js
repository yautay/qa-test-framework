import { describe, expect, it } from "vitest";
import { isAbsoluteUrl, buildReportAssetSrc, buildRefApiSrc } from "../../src/composables/useUrlUtils";

describe("useUrlUtils", () => {
  describe("isAbsoluteUrl", () => {
    it("returns true for http URLs", () => {
      expect(isAbsoluteUrl("http://example.com")).toBe(true);
    });

    it("returns true for https URLs", () => {
      expect(isAbsoluteUrl("https://example.com")).toBe(true);
    });

    it("returns true for data URLs", () => {
      expect(isAbsoluteUrl("data:image/png;base64,abc123")).toBe(true);
    });

    it("returns true for blob URLs", () => {
      expect(isAbsoluteUrl("blob:http://example.com/uuid")).toBe(true);
    });

    it("returns false for relative paths", () => {
      expect(isAbsoluteUrl("/path/to/file.png")).toBe(false);
    });

    it("returns false for relative file names", () => {
      expect(isAbsoluteUrl("file.png")).toBe(false);
    });

    it("handles empty input", () => {
      expect(isAbsoluteUrl("")).toBe(false);
    });

    it("handles null input", () => {
      expect(isAbsoluteUrl(null)).toBe(false);
    });

    it("handles undefined input", () => {
      expect(isAbsoluteUrl(undefined)).toBe(false);
    });

    it("handles whitespace input", () => {
      expect(isAbsoluteUrl("  ")).toBe(false);
    });
  });

  describe("buildReportAssetSrc", () => {
    it("returns empty string for empty path", () => {
      expect(buildReportAssetSrc("run-1", "")).toBe("");
    });

    it("returns empty string for null path", () => {
      expect(buildReportAssetSrc("run-1", null)).toBe("");
    });

    it("returns absolute URLs unchanged", () => {
      expect(buildReportAssetSrc("run-1", "http://example.com/img.png")).toBe("http://example.com/img.png");
      expect(buildReportAssetSrc("run-1", "https://example.com/img.png")).toBe("https://example.com/img.png");
    });

    it("returns paths starting with / unchanged", () => {
      expect(buildReportAssetSrc("run-1", "/path/to/file.png")).toBe("/path/to/file.png");
    });

    it("builds correct path for relative paths", () => {
      expect(buildReportAssetSrc("run-1", "actual/result.png")).toBe("/reports/run-1/actual/result.png");
    });

    it("encodes run ID properly", () => {
      expect(buildReportAssetSrc("run-123", "file.png")).toBe("/reports/run-123/file.png");
    });

    it("handles empty run ID", () => {
      expect(buildReportAssetSrc("", "file.png")).toBe("file.png");
    });
  });

  describe("buildRefApiSrc", () => {
    it("returns empty string when no runId", () => {
      const row = { suite_id: "s1", scenario_id: "sc1", viewport: "1920x1080", browser: "chrome" };
      expect(buildRefApiSrc("", row)).toBe("");
    });

    it("returns empty string when no row", () => {
      expect(buildRefApiSrc("run-1", null)).toBe("");
    });

    it("returns empty string when missing suite_id", () => {
      const row = { scenario_id: "sc1", viewport: "1920x1080", browser: "chrome" };
      expect(buildRefApiSrc("run-1", row)).toBe("");
    });

    it("returns empty string when missing scenario_id", () => {
      const row = { suite_id: "s1", viewport: "1920x1080", browser: "chrome" };
      expect(buildRefApiSrc("run-1", row)).toBe("");
    });

    it("returns empty string when missing viewport", () => {
      const row = { suite_id: "s1", scenario_id: "sc1", browser: "chrome" };
      expect(buildRefApiSrc("run-1", row)).toBe("");
    });

    it("returns empty string when missing browser", () => {
      const row = { suite_id: "s1", scenario_id: "sc1", viewport: "1920x1080" };
      expect(buildRefApiSrc("run-1", row)).toBe("");
    });

    it("builds correct URL with all parameters", () => {
      const row = { suite_id: "suite1", scenario_id: "scenario1", viewport: "1920x1080", browser: "chrome" };
      const result = buildRefApiSrc("run-123", row);
      expect(result).toContain("/api/reports/run-123/image/ref?");
      expect(result).toContain("suite_id=suite1");
      expect(result).toContain("scenario_id=scenario1");
      expect(result).toContain("viewport=1920x1080");
      expect(result).toContain("browser=chrome");
    });

    it("handles empty string values in row", () => {
      const row = { suite_id: "", scenario_id: "sc1", viewport: "1920x1080", browser: "chrome" };
      expect(buildRefApiSrc("run-1", row)).toBe("");
    });
  });
});
