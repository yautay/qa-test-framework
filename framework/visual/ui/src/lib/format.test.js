import { describe, expect, it } from "vitest";

import { fmt, summaryFor } from "./format";

describe("format", () => {
  describe("fmt", () => {
    it("formats integer with default 6 digits", () => {
      expect(fmt(123)).toBe("123");
    });

    it("formats decimal with trailing zeros trimmed", () => {
      expect(fmt(1.5)).toBe("1.5");
      expect(fmt(1.500000)).toBe("1.5");
    });

    it("rounds and trims trailing zeros", () => {
      expect(fmt(1.23456789)).toBe("1.234568");
      expect(fmt(1.100000)).toBe("1.1");
      expect(fmt(1.000000)).toBe("1");
    });

    it("returns empty string for null/undefined/empty", () => {
      expect(fmt(null)).toBe("");
      expect(fmt(undefined)).toBe("");
      expect(fmt("")).toBe("");
    });

    it("returns empty string for non-finite numbers", () => {
      expect(fmt(NaN)).toBe("");
      expect(fmt(Infinity)).toBe("");
      expect(fmt(-Infinity)).toBe("");
    });

    it("accepts custom digit parameter", () => {
      expect(fmt(1.23456789, 2)).toBe("1.23");
      expect(fmt(1.999, 2)).toBe("2");
      expect(fmt(1.000001, 3)).toBe("1");
    });

    it("handles negative numbers", () => {
      expect(fmt(-1.5)).toBe("-1.5");
      expect(fmt(-1.234567, 3)).toBe("-1.235");
    });

    it("handles zero", () => {
      expect(fmt(0)).toBe("0");
      expect(fmt(0.0)).toBe("0");
      expect(fmt(0.000001, 6)).toBe("0.000001");
    });
  });

  describe("summaryFor", () => {
    it("counts statuses with error/new mapped to failed", () => {
      const rows = [
        { status: "passed" },
        { status: "passed" },
        { status: "failed" },
        { status: "skipped" },
        { status: "error" },
        { status: "new" },
      ];

      const result = summaryFor(rows);

      expect(result).toContain("total=6");
      expect(result).toContain("passed=2");
      expect(result).toContain("failed=3");
      expect(result).toContain("skipped=1");
    });

    it("handles empty array", () => {
      const result = summaryFor([]);

      expect(result).toBe("total=0 passed=0 failed=0 skipped=0");
    });

    it("handles rows without status", () => {
      const rows = [
        { scenario_id: "s1" },
        { status: null },
        { status: undefined },
      ];

      const result = summaryFor(rows);

      expect(result).toContain("total=3");
      expect(result).toContain("passed=0");
      expect(result).toContain("failed=0");
    });
  });
});
