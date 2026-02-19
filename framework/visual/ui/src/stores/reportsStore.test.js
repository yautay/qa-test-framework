import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useReportsStore } from "./reportsStore";

vi.mock("../lib/api/reportsApi", () => ({
  fetchReportsList: vi.fn(async () => [
    { run_id: "run-1", tester: "jan.k", summary: "failed=2 passed=3" },
    { run_id: "run-2", tester: "ola.z", summary: "failed=0 passed=4" },
  ]),
}));

describe("reportsStore", () => {
  let pinia;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("initializes with empty reports and default values", () => {
      const store = useReportsStore();

      expect(store.reports).toEqual([]);
      expect(store.query).toBe("");
      expect(store.selectedTester).toBe("");
      expect(store.refreshInFlight).toBe(false);
      expect(store.refreshTimer).toBe(null);
    });
  });

  describe("fetchReports", () => {
    it("fetches reports and updates state", async () => {
      const store = useReportsStore();

      await store.fetchReports();

      expect(store.reports).toHaveLength(2);
      expect(store.reports[0].run_id).toBe("run-1");
      expect(store.refreshInFlight).toBe(false);
    });

    it("sets reports to empty array on error", async () => {
      const { fetchReportsList } = await import("../lib/api/reportsApi");
      fetchReportsList.mockRejectedValueOnce(new Error("network error"));

      const store = useReportsStore();

      await store.fetchReports();

      expect(store.reports).toEqual([]);
    });

    it("does not fetch if already in flight", async () => {
      const { fetchReportsList } = await import("../lib/api/reportsApi");

      const store = useReportsStore();
      store.refreshInFlight = true;

      await store.fetchReports();

      expect(fetchReportsList).not.toHaveBeenCalled();
    });
  });

  describe("setQuery", () => {
    it("updates query value", () => {
      const store = useReportsStore();

      store.setQuery("test");

      expect(store.query).toBe("test");
    });
  });

  describe("setTester", () => {
    it("updates selectedTester value", () => {
      const store = useReportsStore();

      store.setTester("jan.k");

      expect(store.selectedTester).toBe("jan.k");
    });
  });

  describe("testerOptions", () => {
    it("extracts unique testers from reports", () => {
      const store = useReportsStore();
      store.reports = [
        { tester: "jan.k" },
        { tester: "ola.z" },
        { tester: "jan.k" },
      ];

      expect(store.testerOptions).toEqual(["jan.k", "ola.z"]);
    });

    it("filters out empty testers", () => {
      const store = useReportsStore();
      store.reports = [
        { tester: "jan.k" },
        { tester: "" },
        { tester: "   " },
      ];

      expect(store.testerOptions).toEqual(["jan.k"]);
    });

    it("sorts testers alphabetically", () => {
      const store = useReportsStore();
      store.reports = [
        { tester: "ola.z" },
        { tester: "jan.k" },
        { tester: "marek.a" },
      ];

      expect(store.testerOptions).toEqual(["jan.k", "marek.a", "ola.z"]);
    });
  });

  describe("filteredReports", () => {
    it("returns all reports when no filters applied", () => {
      const store = useReportsStore();
      store.reports = [
        { run_id: "run-1", summary: "failed=2" },
        { run_id: "run-2", summary: "failed=0" },
      ];

      expect(store.filteredReports).toHaveLength(2);
    });

    it("filters by query in run_id", () => {
      const store = useReportsStore();
      store.reports = [
        { run_id: "20260218_120000", summary: "failed=2" },
        { run_id: "20260217_120000", summary: "failed=0" },
      ];
      store.query = "18";

      expect(store.filteredReports).toHaveLength(1);
      expect(store.filteredReports[0].run_id).toBe("20260218_120000");
    });

    it("filters by query in summary", () => {
      const store = useReportsStore();
      store.reports = [
        { run_id: "run-1", summary: "failed=2 passed=3" },
        { run_id: "run-2", summary: "failed=0 passed=4" },
      ];
      store.query = "failed=2";

      expect(store.filteredReports).toHaveLength(1);
      expect(store.filteredReports[0].run_id).toBe("run-1");
    });

    it("filters by query in run_note", () => {
      const store = useReportsStore();
      store.reports = [
        { run_id: "run-1", run_note: "smoke test" },
        { run_id: "run-2", run_note: "" },
      ];
      store.query = "smoke";

      expect(store.filteredReports).toHaveLength(1);
      expect(store.filteredReports[0].run_id).toBe("run-1");
    });

    it("filters by selectedTester", () => {
      const store = useReportsStore();
      store.reports = [
        { run_id: "run-1", tester: "jan.k" },
        { run_id: "run-2", tester: "ola.z" },
      ];
      store.selectedTester = "jan.k";

      expect(store.filteredReports).toHaveLength(1);
      expect(store.filteredReports[0].run_id).toBe("run-1");
    });

    it("combines query and tester filters", () => {
      const store = useReportsStore();
      store.reports = [
        { run_id: "run-1", tester: "jan.k", summary: "failed=2" },
        { run_id: "run-2", tester: "ola.z", summary: "failed=0" },
        { run_id: "run-3", tester: "jan.k", summary: "failed=1" },
      ];
      store.query = "failed";
      store.selectedTester = "jan.k";

      const result = store.filteredReports;

      expect(result).toHaveLength(2);
      expect(result.every(r => r.tester === "jan.k")).toBe(true);
    });

    it("searches case-insensitively", () => {
      const store = useReportsStore();
      store.reports = [
        { run_id: "Run-Test" },
        { run_id: "run-test" },
      ];
      store.query = "RUN";

      expect(store.filteredReports).toHaveLength(2);
    });

    it("trims query whitespace", () => {
      const store = useReportsStore();
      store.reports = [
        { run_id: "run-1" },
        { run_id: "run-2" },
      ];
      store.query = "  run-1  ";

      expect(store.filteredReports).toHaveLength(1);
      expect(store.filteredReports[0].run_id).toBe("run-1");
    });
  });

  describe("auto-refresh", () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    it("starts auto-refresh timer", () => {
      const store = useReportsStore();
      store.startAutoRefresh();

      expect(store.refreshTimer).not.toBeNull();

      store.stopAutoRefresh();
    });

    it("stops auto-refresh timer", () => {
      const store = useReportsStore();
      store.startAutoRefresh();

      store.stopAutoRefresh();

      expect(store.refreshTimer).toBeNull();
    });

    it("fetches reports at intervals", async () => {
      const { fetchReportsList } = await import("../lib/api/reportsApi");

      const store = useReportsStore();
      await store.fetchReports();
      store.startAutoRefresh();

      await vi.advanceTimersByTimeAsync(5000);

      expect(fetchReportsList).toHaveBeenCalledTimes(2);

      store.stopAutoRefresh();
    });
  });
});
