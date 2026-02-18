import { afterEach, describe, expect, it, vi } from "vitest";

import { requestBaselineChallengeForRun, sendBaselineSelectionForRun } from "./baselineApi";

function response(body, ok = true) {
  return {
    ok,
    text: async () => JSON.stringify(body),
  };
}

describe("baselineApi run scoped", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests challenge for selected run", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ challenge_id: "abc", phrase: "hello" })));

    const payload = await requestBaselineChallengeForRun("run 1");

    expect(payload).toEqual({ challenge_id: "abc", phrase: "hello" });
    expect(fetch).toHaveBeenCalledWith("/api/reports/run%201/baseline/challenge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
  });

  it("sends baseline payload for selected run", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ accepted: true })));
    const body = { challenge_id: "abc", phrase: "hello", items: [] };

    const payload = await sendBaselineSelectionForRun("run-2", body);

    expect(payload).toEqual({ accepted: true });
    expect(fetch).toHaveBeenCalledWith("/api/reports/run-2/baseline/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  });
});
