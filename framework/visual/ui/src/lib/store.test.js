import { describe, expect, it } from "vitest";

import { createStore, setRows, filteredSorted, resetFilters } from "./store";

describe("store", () => {
  describe("createStore", () => {
    it("initializes with empty rows and default values", () => {
      const store = createStore();

      expect(store.rows).toEqual([]);
      expect(store.q).toBe("");
      expect(store.status).toBe("");
      expect(store.mode).toBe("");
      expect(store.sortKey).toBe("scenario_id");
      expect(store.summary).toBe("total=0 passed=0 failed=0 skipped=0 error=0 new=0");
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

    it("filters by compare_mode", () => {
      const store = buildStore([
        { scenario_id: "s1", compare_mode: "pixel" },
        { scenario_id: "s2", compare_mode: "lpips" },
        { scenario_id: "s3", compare_mode: "lpips" },
      ]);
      store.mode = "lpips";

      const result = filteredSorted(store);

      expect(result).toHaveLength(2);
      expect(result.every(r => r.compare_mode === "lpips")).toBe(true);
    });

    it("combines multiple filters", () => {
      const store = buildStore([
        { scenario_id: "s1", status: "passed", compare_mode: "pixel" },
        { scenario_id: "s2", status: "failed", compare_mode: "pixel" },
        { scenario_id: "s3", status: "failed", compare_mode: "lpips" },
      ]);
      store.status = "failed";
      store.mode = "lpips";

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
        { scenario_id: "s1", lpips_score: 10 },
        { scenario_id: "s2", lpips_score: 100 },
        { scenario_id: "s3", lpips_score: 1 },
      ]);
      store.sortKey = "lpips_score";

      const result = filteredSorted(store);

      expect(result[0].lpips_score).toBe(100);
      expect(result[1].lpips_score).toBe(10);
      expect(result[2].lpips_score).toBe(1);
    });

    it("handles null values in sort", () => {
      const store = buildStore([
        { scenario_id: "s1", lpips_score: 5 },
        { scenario_id: "s2" },
        { scenario_id: "s3", lpips_score: null },
      ]);
      store.sortKey = "lpips_score";

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
  });

  describe("resetFilters", () => {
    it("resets all filters to default", () => {
      const store = createStore();
      store.q = "search";
      store.status = "failed";
      store.mode = "lpips";
      store.sortKey = "lpips_score";

      resetFilters(store);

      expect(store.q).toBe("");
      expect(store.status).toBe("");
      expect(store.mode).toBe("");
      expect(store.sortKey).toBe("scenario_id");
    });
  });
});
