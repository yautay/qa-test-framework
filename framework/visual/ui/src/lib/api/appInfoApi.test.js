import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchAppInfo } from "./appInfoApi";

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

describe("appInfoApi", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches app info successfully", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ name: "visual-report", version: "1.0.0" })));

    const result = await fetchAppInfo();

    expect(result).toEqual({ name: "visual-report", version: "1.0.0" });
    expect(fetch).toHaveBeenCalledWith("/api/app-info", { cache: "no-store" });
  });

  it("throws readable error for failed fetch with error field", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ error: "service unavailable" }, false, 500)));

    await expect(fetchAppInfo()).rejects.toThrow("service unavailable");
  });

  it("throws default error for failed fetch without specific error", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({}, false, 500)));

    await expect(fetchAppInfo()).rejects.toThrow("unable to fetch app info");
  });

  it("returns empty object for invalid payload", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => responseText("not-json", true, 200)));

    const result = await fetchAppInfo();

    expect(result).toEqual({});
  });

  it("returns empty object for non-object valid JSON", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response("string", true, 200)));

    const result = await fetchAppInfo();

    expect(result).toEqual({});
  });

  it("returns object when payload is valid object", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response({ appName: "test", build: "123" }, true, 200)));

    const result = await fetchAppInfo();

    expect(result).toEqual({ appName: "test", build: "123" });
  });
});
