import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  loadTagSnapshot,
  saveTagSnapshotToFile,
} from "./tagPersistence";

const TAG_FILE_NAME = "vrt-tags.json";

function mockResponse(ok = true, json = null) {
  return {
    ok,
    json: async () => json,
    text: async () => json ? JSON.stringify(json) : "",
  };
}

describe("tagPersistence", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("loadTagSnapshot", () => {
    it("returns null when file is unavailable", async () => {
      fetch.mockResolvedValue(mockResponse(false));

      const result = await loadTagSnapshot();

      expect(result).toBeNull();
    });

    it("loads snapshot from file", async () => {
      const fileData = { "key1": { bug: true } };
      fetch.mockResolvedValue(mockResponse(true, fileData));

      const result = await loadTagSnapshot();

      expect(result).toEqual({ key1: { bug: true } });
    });
  });

  describe("saveTagSnapshotToFile", () => {
    it("sends PUT request to save file", async () => {
      fetch.mockResolvedValue(mockResponse(true));
      const tagLog = { key1: { bug: true } };

      const result = await saveTagSnapshotToFile(tagLog);

      expect(result).toBe(true);
      expect(fetch).toHaveBeenCalledWith(TAG_FILE_NAME, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tagLog, null, 2),
      });
    });

    it("returns false on network failure", async () => {
      fetch.mockRejectedValue(new Error("network"));

      const result = await saveTagSnapshotToFile({ key: {} });

      expect(result).toBe(false);
    });

    it("returns false for non-ok response", async () => {
      fetch.mockResolvedValue(mockResponse(false));

      const result = await saveTagSnapshotToFile({ key: {} });

      expect(result).toBe(false);
    });

    it("returns false for invalid input", async () => {
      const result1 = await saveTagSnapshotToFile(null);
      const result2 = await saveTagSnapshotToFile(undefined);
      const result3 = await saveTagSnapshotToFile("string");

      expect(result1).toBe(false);
      expect(result2).toBe(false);
      expect(result3).toBe(false);
    });
  });
});
