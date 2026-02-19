import { describe, expect, it } from "vitest";

import { createStore, setRows, filteredSorted, resetFilters } from "./store";

describe("store", () => {
  describe("createStore", () => {
    it("initializes with empty rows and default values", () => {
      const store = createStore();

      expect(store.rows).toEqual([]);
      expect(store.q).toBe("");
      expect(store.status).toBe("");
      expect(store.viewport).toBe("");
      expect(store.sortKey).toBe("scenario_id");
      expect(store.summary).toBe("total=0 passed=0 failed=0 skipped=0");
    });
  });

  describe("setRows", () => {
    it("sets rows and updates summary", () => {
      const store = createStore();
      const rows = [
        { scenario_id: "s1", status: "passed" },
        { scenario_id: "s2", status: "failed" },
        { scenario_id: "s3", status: "passed" },
      ];

      setRows(store, rows);

      expect(store.rows).toHaveLength(3);
      expect(store.summary).toContain("total=3");
      expect(store.summary).toContain("passed=2");
      expect(store.summary).toContain("failed=1");
    });

    it("normalizes error and new statuses to failed", () => {
      const store = createStore();
      const rows = [
        { scenario_id: "s1", status: "error" },
        { scenario_id: "s2", status: "new" },
      ];

      setRows(store, rows);

      expect(store.rows[0].status).toBe("failed");
      expect(store.rows[1].status).toBe("failed");
      expect(store.summary).toContain("failed=2");
    });

    it("handles non-array input", () => {
      const store = createStore();

      setRows(store, null);
      expect(store.rows).toEqual([]);

      setRows(store, undefined);
      expect(store.rows).toEqual([]);

      setRows(store, "not an array");
      expect(store.rows).toEqual([]);
    });
  });

  describe("filteredSorted", () => {
    const buildStore = (rows) => {
      const store = createStore();
      setRows(store, rows);
      return store;
    };

    it("returns all rows when no filters applied", () => {
      const store = buildStore([
        { scenario_id: "a", status: "passed" },
        { scenario_id: "b", status: "failed" },
      ]);

      const result = filteredSorted(store);

      expect(result).toHaveLength(2);
    });

    it("filters by query in scenario_id", () => {
      const store = buildStore([
        { scenario_id: "login-test", status: "passed" },
        { scenario_id: "logout-test", status: "passed" },
        { scenario_id: "profile-test", status: "failed" },
      ]);
      store.q = "login";

      const result = filteredSorted(store);

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("login-test");
    });

    it("filters by query in message", () => {
      const store = buildStore([
        { scenario_id: "s1", message: "timeout error" },
        { scenario_id: "s2", message: "success" },
      ]);
      store.q = "timeout";

      const result = filteredSorted(store);

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("s1");
    });

    it("filters by status", () => {
      const store = buildStore([
        { scenario_id: "s1", status: "passed" },
        { scenario_id: "s2", status: "failed" },
        { scenario_id: "s3", status: "failed" },
      ]);
      store.status = "failed";

      const result = filteredSorted(store);

      expect(result).toHaveLength(2);
      expect(result.every(r => r.status === "failed")).toBe(true);
    });

    it("filters by viewport", () => {
      const store = buildStore([
        { scenario_id: "s1", viewport: "fhd" },
        { scenario_id: "s2", viewport: "2k" },
        { scenario_id: "s3", viewport: "fhd" },
      ]);
      store.viewport = "fhd";

      const result = filteredSorted(store);

      expect(result).toHaveLength(2);
      expect(result.every(r => r.viewport === "fhd")).toBe(true);
    });

    it("filters by browser", () => {
      const store = buildStore([
        { scenario_id: "s1", browser: "chromium" },
        { scenario_id: "s2", browser: "firefox" },
        { scenario_id: "s3", browser: "chromium" },
      ]);
      store.browser = "chromium";

      const result = filteredSorted(store);

      expect(result).toHaveLength(2);
      expect(result.every(r => r.browser === "chromium")).toBe(true);
    });

    it("combines multiple filters", () => {
      const store = buildStore([
        { scenario_id: "s1", status: "passed" },
        { scenario_id: "s2", status: "failed" },
        { scenario_id: "s3", status: "failed" },
      ]);
      store.status = "failed";
      store.q = "s3";

      store.browser = "";

      const result = filteredSorted(store);

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("s3");
    });

    it("sorts by scenario_id ascending by default", () => {
      const store = buildStore([
        { scenario_id: "z-test" },
        { scenario_id: "a-test" },
        { scenario_id: "m-test" },
      ]);

      const result = filteredSorted(store);

      expect(result[0].scenario_id).toBe("a-test");
      expect(result[1].scenario_id).toBe("m-test");
      expect(result[2].scenario_id).toBe("z-test");
    });

    it("sorts numerically descending for numeric keys", () => {
      const store = buildStore([
        { scenario_id: "s1", lpips: 0.1 },
        { scenario_id: "s2", lpips: 1.0 },
        { scenario_id: "s3", lpips: 0.01 },
      ]);
      store.sortKey = "lpips";

      const result = filteredSorted(store);

      expect(result[0].lpips).toBe(1.0);
      expect(result[1].lpips).toBe(0.1);
      expect(result[2].lpips).toBe(0.01);
    });

    it("sorts status by priority (failed, skipped, passed)", () => {
      const store = buildStore([
        { scenario_id: "s1", status: "passed" },
        { scenario_id: "s2", status: "failed" },
        { scenario_id: "s3", status: "skipped" },
      ]);
      store.sortKey = "status";

      const result = filteredSorted(store);

      expect(result[0].status).toBe("failed");
      expect(result[1].status).toBe("skipped");
      expect(result[2].status).toBe("passed");
    });

    it("handles null values in sort", () => {
      const store = buildStore([
        { scenario_id: "s1", lpips: 0.5 },
        { scenario_id: "s2" },
        { scenario_id: "s3", lpips: null },
      ]);
      store.sortKey = "lpips";

      const result = filteredSorted(store);

      expect(result[0].scenario_id).toBe("s1");
      expect(result[1].scenario_id).not.toBe("s1");
      expect(result[2].scenario_id).not.toBe("s1");
    });

    it("trims query whitespace", () => {
      const store = buildStore([
        { scenario_id: "test-a" },
        { scenario_id: "test-b" },
      ]);
      store.q = "  test-a  ";

      const result = filteredSorted(store);

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("test-a");
    });

    it("searches case-insensitively", () => {
      const store = buildStore([
        { scenario_id: "Login-Test" },
        { scenario_id: "logout-test" },
      ]);
      store.q = "LOGIN";

      const result = filteredSorted(store);

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("Login-Test");
    });

    it("sorts by tags priority (bug > aso > baseline > none)", () => {
      const store = buildStore([
        { scenario_id: "s1", status: "passed", actual_path: "a.png", baseline_path: "", diff_path: "" },
        { scenario_id: "s2", status: "failed", actual_path: "b.png", baseline_path: "", diff_path: "" },
        { scenario_id: "s3", status: "failed", actual_path: "c.png", baseline_path: "", diff_path: "" },
      ]);
      store.sortKey = "tags";

      const tagLog = {
        "s2::b.png::::": { bug: true },
        "s3::c.png::::": {aso: true },
      };

      const result = filteredSorted(store, tagLog);

      expect(result[0].scenario_id).toBe("s2");
      expect(result[1].scenario_id).toBe("s3");
      expect(result[2].scenario_id).toBe("s1");
    });

    it("filters by status and browser together", () => {
      const store = buildStore([
        { scenario_id: "s1", status: "failed", browser: "firefox" },
        { scenario_id: "s2", status: "failed", browser: "chromium" },
        { scenario_id: "s3", status: "passed", browser: "chromium" },
      ]);
      store.status = "failed";
      store.browser = "chromium";

      const result = filteredSorted(store);

      expect(result).toHaveLength(1);
      expect(result[0].scenario_id).toBe("s2");
    });
  });

  describe("resetFilters", () => {
    it("resets all filters to default", () => {
      const store = createStore();
      store.q = "search";
      store.status = "failed";
      store.viewport = "fhd";
      store.browser = "chromium";
      store.sortKey = "lpips";

      resetFilters(store);

      expect(store.q).toBe("");
      expect(store.status).toBe("");
      expect(store.viewport).toBe("");
      expect(store.browser).toBe("");
      expect(store.sortKey).toBe("scenario_id");
    });
  });
});
