import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  loadTagSnapshot,
  persistTagSnapshot,
  saveTagSnapshotToFile,
  downloadTagSnapshot,
  parseTagFile,
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
  let localStorageMock;

  beforeEach(() => {
    localStorageMock = {
      data: {},
      getItem(key) {
        return this.data[key] || null;
      },
      setItem(key, value) {
        this.data[key] = value;
      },
      removeItem(key) {
        delete this.data[key];
      },
    };
    vi.stubGlobal("localStorage", localStorageMock);
    vi.stubGlobal("location", { pathname: "/test" });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("loadTagSnapshot", () => {
    it("returns null when neither file nor storage has data", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => mockResponse(false)));

      const result = await loadTagSnapshot();

      expect(result).toBeNull();
    });

    it("loads from file when available", async () => {
      const fileData = { "key1": { bug: true } };
      vi.stubGlobal("fetch", vi.fn(async () => mockResponse(true, fileData)));

      const result = await loadTagSnapshot();

      expect(result).toEqual({ key1: { bug: true } });
    });

    it("loads from storage when file unavailable", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => mockResponse(false)));
      localStorageMock.data["vrt-tag-log:/test"] = JSON.stringify({ key2: { baseline: true } });

      const result = await loadTagSnapshot();

      expect(result).toEqual({ key2: { baseline: true } });
    });

    it("merges file and storage data (file takes precedence)", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => mockResponse(true, { fromFile: { bug: true } })));
      localStorageMock.data["vrt-tag-log:/test"] = JSON.stringify({ fromStorage: { baseline: true } });

      const result = await loadTagSnapshot();

      expect(result).toEqual({ fromFile: { bug: true }, fromStorage: { baseline: true } });
    });

    it("falls back to legacy storage key", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => mockResponse(false)));
      localStorageMock.data["vrt-tag-log"] = JSON.stringify({ legacy: { bug: true } });

      const result = await loadTagSnapshot();

      expect(result).toEqual({ legacy: { bug: true } });
    });
  });

  describe("persistTagSnapshot", () => {
    it("saves to localStorage", () => {
      const tagLog = { key1: { bug: true }, key2: { baseline: false } };

      persistTagSnapshot(tagLog);

      expect(localStorageMock.data["vrt-tag-log:/test"]).toBe(JSON.stringify(tagLog));
    });

    it("does nothing for invalid input", () => {
      persistTagSnapshot(null);
      persistTagSnapshot(undefined);
      persistTagSnapshot("string");
      persistTagSnapshot(123);

      expect(localStorageMock.data).toEqual({});
    });
  });

  describe("saveTagSnapshotToFile", () => {
    it("sends PUT request to save file", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => mockResponse(true)));
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
      vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("network"))));

      const result = await saveTagSnapshotToFile({ key: {} });

      expect(result).toBe(false);
    });

    it("returns false for non-ok response", async () => {
      vi.stubGlobal("fetch", vi.fn(async () => mockResponse(false)));

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

  describe("downloadTagSnapshot", () => {
    beforeEach(() => {
      vi.stubGlobal("document", {
        body: {
          appendChild: vi.fn(),
          removeChild: vi.fn(),
        },
        createElement: vi.fn((tag) => ({
          tagName: tag.toUpperCase(),
          href: "",
          download: "",
          click: vi.fn(),
        })),
      });
      vi.stubGlobal("URL", {
        createObjectURL: vi.fn(() => "blob:http://test"),
        revokeObjectURL: vi.fn(),
      });
      vi.stubGlobal("Blob", vi.fn((data, options) => ({ data, options })));
    });

    it("creates download link and triggers click", () => {
      const tagLog = { key: { bug: true } };

      downloadTagSnapshot(tagLog);

      expect(document.createElement).toHaveBeenCalledWith("a");
      expect(URL.createObjectURL).toHaveBeenCalled();
      expect(document.body.appendChild).toHaveBeenCalled();
      expect(document.body.removeChild).toHaveBeenCalled();
      expect(URL.revokeObjectURL).toHaveBeenCalled();
    });

    it("does nothing for invalid input", () => {
      downloadTagSnapshot(null);
      downloadTagSnapshot(undefined);
      downloadTagSnapshot("string");

      expect(document.createElement).not.toHaveBeenCalled();
    });
  });

  describe("parseTagFile", () => {
    it("parses valid JSON file", async () => {
      const file = {
        text: vi.fn(async () => JSON.stringify({ key: { bug: true } })),
      };

      const result = await parseTagFile(file);

      expect(result).toEqual({ key: { bug: true } });
    });

    it("returns null for empty file", async () => {
      const file = {
        text: vi.fn(async () => ""),
      };

      const result = await parseTagFile(file);

      expect(result).toBeNull();
    });

    it("returns null for invalid JSON", async () => {
      const file = {
        text: vi.fn(async () => "not valid json {"),
      };

      const result = await parseTagFile(file);

      expect(result).toBeNull();
    });

    it("returns null for null input", async () => {
      const result = await parseTagFile(null);
      const result2 = await parseTagFile(undefined);

      expect(result).toBeNull();
      expect(result2).toBeNull();
    });

    it("returns null for non-object JSON", async () => {
      const file = {
        text: vi.fn(async () => "123"),
      };

      const result = await parseTagFile(file);

      expect(result).toBeNull();
    });
  });
});
