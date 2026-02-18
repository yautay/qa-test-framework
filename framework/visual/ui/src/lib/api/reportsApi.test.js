import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchReportResults, fetchReportsList } from "./reportsApi";

function response(body, ok = true, status = 200) {
  return {
    ok,
    status,
    text: async () => JSON.stringify(body),
  };
}

describe("reportsApi", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches reports list", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ reports: [{ run_id: "run-1" }] })));

    const reports = await fetchReportsList();

    expect(reports).toEqual([{ run_id: "run-1" }]);
    expect(fetch).toHaveBeenCalledWith("/api/reports", { cache: "no-store" });
  });

  it("throws readable error for failed reports list", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ error: "boom" }, false, 500)));

    await expect(fetchReportsList()).rejects.toThrow("boom");
  });

  it("fetches report results for encoded run id", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ results: [{ scenario_id: "s-1" }] })));

    const results = await fetchReportResults("run 1");

    expect(results).toEqual([{ scenario_id: "s-1" }]);
    expect(fetch).toHaveBeenCalledWith("/api/reports/run%201/results", { cache: "no-store" });
  });

  it("throws readable error for failed report results", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ error: "missing" }, false, 404)));

    await expect(fetchReportResults("run-404")).rejects.toThrow("missing");
  });
});
