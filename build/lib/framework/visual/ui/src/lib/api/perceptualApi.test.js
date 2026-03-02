import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchPerceptualQueue, fetchPerceptualHealth } from "./perceptualApi";

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

describe("perceptualApi", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchPerceptualQueue", () => {
    it("fetches perceptual queue successfully", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => response({ queue: ["item-1", "item-2"] })));

      const result = await fetchPerceptualQueue();

      expect(result).toEqual({ queue: ["item-1", "item-2"] });
      expect(fetch).toHaveBeenCalledWith("/api/perceptual/queue", { cache: "no-store" });
    });

    it("throws readable error for failed queue fetch with error field", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => response({ error: "queue unavailable" }, false, 500)));

      await expect(fetchPerceptualQueue()).rejects.toThrow("queue unavailable");
    });

    it("throws readable error for failed queue fetch with error_message field", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => response({ error_message: "service down" }, false, 503)));

      await expect(fetchPerceptualQueue()).rejects.toThrow("service down");
    });

    it("throws default error for failed queue fetch with unknown error", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => response({}, false, 500)));

      await expect(fetchPerceptualQueue()).rejects.toThrow("unable to fetch perceptual queue");
    });

    it("returns empty object for invalid queue payload", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => responseText("not-json", true, 200)));

      const result = await fetchPerceptualQueue();

      expect(result).toEqual({});
    });

    it("returns valid payload when it's a non-object primitive", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => response("string", true, 200)));

      const result = await fetchPerceptualQueue();

      expect(result).toEqual({});
    });
  });

  describe("fetchPerceptualHealth", () => {
    it("fetches perceptual health successfully", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => response({ status: "healthy", checks: [] })));

      const result = await fetchPerceptualHealth();

      expect(result).toEqual({ status: "healthy", checks: [] });
      expect(fetch).toHaveBeenCalledWith("/api/perceptual/health", { cache: "no-store" });
    });

    it("throws readable error for failed health fetch with error field", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => response({ error: "health check failed" }, false, 500)));

      await expect(fetchPerceptualHealth()).rejects.toThrow("health check failed");
    });

    it("throws readable error for failed health fetch with error_message field", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => response({ error_message: "unhealthy" }, false, 503)));

      await expect(fetchPerceptualHealth()).rejects.toThrow("unhealthy");
    });

    it("throws default error for failed health fetch with unknown error", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => response({}, false, 500)));

      await expect(fetchPerceptualHealth()).rejects.toThrow("unable to fetch perceptual health");
    });

    it("returns empty object for invalid health payload", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => responseText("not-json", true, 200)));

      const result = await fetchPerceptualHealth();

      expect(result).toEqual({});
    });
  });
});
