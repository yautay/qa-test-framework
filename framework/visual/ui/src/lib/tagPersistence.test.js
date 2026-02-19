import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  loadTagSnapshot,
  saveTagSnapshotToFile,
} from "./tagPersistence";

const RUN_ID = "test-run";
const TAG_FILE_NAME = "vrt-tags.json";
const TAG_FILE_URL = `/reports/${encodeURIComponent(RUN_ID)}/${TAG_FILE_NAME}`;

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

      const result = await loadTagSnapshot(RUN_ID);

      expect(result).toBeNull();
      expect(fetch).toHaveBeenCalledWith(TAG_FILE_URL, { cache: "no-store" });
    });

    it("loads snapshot from file", async () => {
      const fileData = { "key1": { bug: true } };
      fetch.mockResolvedValue(mockResponse(true, fileData));

      const result = await loadTagSnapshot(RUN_ID);

      expect(result).toEqual({ key1: { bug: true } });
      expect(fetch).toHaveBeenCalledWith(TAG_FILE_URL, { cache: "no-store" });
    });
  });

  describe("saveTagSnapshotToFile", () => {
    it("sends PUT request to save file", async () => {
      fetch.mockResolvedValue(mockResponse(true));
      const tagLog = { key1: { bug: true } };

      const result = await saveTagSnapshotToFile(tagLog, RUN_ID);

      expect(result).toBe(true);
      expect(fetch).toHaveBeenCalledWith(TAG_FILE_URL, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tagLog, null, 2),
      });
    });

    it("persists note payload in snapshot", async () => {
      fetch.mockResolvedValue(mockResponse(true));
      const tagLog = {
        key1: {
          bug: false,
          aso: false,
          baseline: false,
          note: {
            text: "Needs manual verification",
            updatedAt: "2026-02-19T12:30:00.000Z",
          },
        },
      };

      const result = await saveTagSnapshotToFile(tagLog, RUN_ID);

      expect(result).toBe(true);
      expect(fetch).toHaveBeenCalledWith(TAG_FILE_URL, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tagLog, null, 2),
      });
    });

    it("returns false on network failure", async () => {
      fetch.mockRejectedValue(new Error("network"));

      const result = await saveTagSnapshotToFile({ key: {} }, RUN_ID);

      expect(result).toBe(false);
    });

    it("returns false for non-ok response", async () => {
      fetch.mockResolvedValue(mockResponse(false));

      const result = await saveTagSnapshotToFile({ key: {} }, RUN_ID);

      expect(result).toBe(false);
    });

    it("returns false for invalid input", async () => {
      const result1 = await saveTagSnapshotToFile(null, RUN_ID);
      const result2 = await saveTagSnapshotToFile(undefined, RUN_ID);
      const result3 = await saveTagSnapshotToFile("string", RUN_ID);

      expect(result1).toBe(false);
      expect(result2).toBe(false);
      expect(result3).toBe(false);
    });
  });
});
