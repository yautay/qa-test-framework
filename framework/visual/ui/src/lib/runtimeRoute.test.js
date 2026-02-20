import { describe, expect, it } from "vitest";

import { parseRuntimeRoute, reportPath } from "./runtimeRoute";

describe("runtimeRoute", () => {
  it("returns hero route for root paths", () => {
    expect(parseRuntimeRoute("/")).toEqual({ page: "hero", runId: "" });
    expect(parseRuntimeRoute("/index.html")).toEqual({ page: "hero", runId: "" });
  });

  it("parses report route with run id", () => {
    expect(parseRuntimeRoute("/reports/20260218_120000_000001")).toEqual({
      page: "report",
      runId: "20260218_120000_000001",
    });

    expect(parseRuntimeRoute("/reports/20260218_120000_000001/index.html")).toEqual({
      page: "report",
      runId: "20260218_120000_000001",
    });
  });

  it("decodes encoded run id", () => {
    expect(parseRuntimeRoute("/reports/run%20123")).toEqual({ page: "report", runId: "run 123" });
  });

  it("falls back to hero for unknown path", () => {
    expect(parseRuntimeRoute("/unknown")).toEqual({ page: "hero", runId: "" });
  });

  it("builds report path from run id", () => {
    expect(reportPath("20260218")).toBe("/reports/20260218");
    expect(reportPath("run 123")).toBe("/reports/run%20123");
    expect(reportPath("")).toBe("/");
  });
});
