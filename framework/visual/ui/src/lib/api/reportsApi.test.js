import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchReportResults, fetchReportsList, sendRunReport } from "./reportsApi";

function response(body, ok = true, status = 200) {
  return {
    ok,
    status,
    text: async () => JSON.stringify(body),
  };
}

function responseText(text, ok = true, status = 200) {
  return {
    ok,
    status,
    text: async () => text,
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

  it("returns empty list for invalid reports payload", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => responseText("not-json", true, 200)));

    const reports = await fetchReportsList();

    expect(reports).toEqual([]);
  });

  it("uses fallback message when reports list error payload is invalid", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => responseText("not-json", false, 500)));

    await expect(fetchReportsList()).rejects.toThrow("unable to fetch reports");
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

  it("returns empty results for invalid payload", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => responseText("not-json", true, 200)));

    const results = await fetchReportResults("run-1");

    expect(results).toEqual([]);
  });

  it("sends run report payload", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ accepted: true, bug: { sent: 1 } })));

    const payload = await sendRunReport("run 1", { tag_snapshot: { a: { bug: true } } });
    const SignalCtor = globalThis.AbortSignal || Object;

    expect(payload.accepted).toBe(true);
    expect(fetch).toHaveBeenCalledWith("/api/reports/run%201/report/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tag_snapshot: { a: { bug: true } } }),
      signal: expect.any(SignalCtor),
    });
  });
});
