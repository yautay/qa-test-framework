import { afterEach, describe, expect, it, vi } from "vitest";

import {
  fetchReportResults,
  fetchReportResultsPayload,
  fetchReportsList,
  fetchBuildTags,
  postBuildEvent,
  acquireBuildLock,
  heartbeatBuildLock,
  releaseBuildLock,
  sendBuildReport,
} from "./reportsApi";

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

  it("returns report results payload with build metadata", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response({
          run_id: "run-1",
          results: [{ scenario_id: "s-1" }],
          build_metadata: { visual: { excluded_count: 1 } },
        })
      )
    );

    const payload = await fetchReportResultsPayload("run-1");

    expect(payload.run_id).toBe("run-1");
    expect(payload.results).toEqual([{ scenario_id: "s-1" }]);
    expect(payload.build_metadata.visual.excluded_count).toBe(1);
  });

  it("fetches build tags", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ tags: { test_cases: {} } })));

    const payload = await fetchBuildTags("run-1");

    expect(payload.tags).toBeDefined();
    expect(fetch).toHaveBeenCalledWith("/api/builds/run-1/tags", { cache: "no-store" });
  });

  it("throws fallback error for invalid failed build tags payload", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => responseText("not-json", false, 500)));

    await expect(fetchBuildTags("run-1")).rejects.toThrow("unable to fetch build tags");
  });

  it("posts build event", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ accepted: true })));
    const SignalCtor = globalThis.AbortSignal || Object;

    const payload = await postBuildEvent("run 1", { event_id: "e1", type: "BUG_SET" });

    expect(payload.accepted).toBe(true);
    expect(fetch).toHaveBeenCalledWith("/api/builds/run%201/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_id: "e1", type: "BUG_SET" }),
      signal: expect.any(SignalCtor),
    });
  });

  it("acquires build lock", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ accepted: true })));
    const SignalCtor = globalThis.AbortSignal || Object;

    const payload = await acquireBuildLock("run 1", "client-1");

    expect(payload.accepted).toBe(true);
    expect(fetch).toHaveBeenCalledWith("/api/builds/run%201/lock/acquire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: "client-1" }),
      signal: expect.any(SignalCtor),
    });
  });

  it("sends lock heartbeat", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ accepted: true })));
    const SignalCtor = globalThis.AbortSignal || Object;

    const payload = await heartbeatBuildLock("run 1", "client-1", "lock-1");

    expect(payload.accepted).toBe(true);
    expect(fetch).toHaveBeenCalledWith("/api/builds/run%201/lock/heartbeat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: "client-1", lock_id: "lock-1" }),
      signal: expect.any(SignalCtor),
    });
  });

  it("releases build lock", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ accepted: true })));
    const SignalCtor = globalThis.AbortSignal || Object;

    const payload = await releaseBuildLock("run 1", "client-1", "lock-1");

    expect(payload.accepted).toBe(true);
    expect(fetch).toHaveBeenCalledWith("/api/builds/run%201/lock/release", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: "client-1", lock_id: "lock-1" }),
      signal: expect.any(SignalCtor),
    });
  });

  it("sends build report", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ accepted: true, pdf: { pages: 0 } })));
    const SignalCtor = globalThis.AbortSignal || Object;

    const payload = await sendBuildReport("run 1");

    expect(payload.accepted).toBe(true);
    expect(fetch).toHaveBeenCalledWith("/api/builds/run%201/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
      signal: expect.any(SignalCtor),
    });
  });

  it("maps network TypeError to no response error", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new TypeError("network down");
    }));

    await expect(postBuildEvent("run-1", { event_id: "e1" })).rejects.toMatchObject({
      message: "no response from server",
      code: "NO_RESPONSE",
      isNoResponse: true,
    });
  });
});
