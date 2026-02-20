import { defineStore } from "pinia";
import { fetchReportsList } from "../lib/api/reportsApi";

const REPORTS_REFRESH_INTERVAL_MS = 5000;

export const useReportsStore = defineStore("reports", {
  state: () => ({
    reports: [],
    query: "",
    selectedTester: "",
    refreshTimer: null,
    refreshInFlight: false,
  }),

  getters: {
    testerOptions: (state) => {
      const unique = new Set();
      for (const item of state.reports) {
        const tester = String(item?.tester || "").trim();
        if (tester) unique.add(tester);
      }
      return Array.from(unique).sort((a, b) => a.localeCompare(b));
    },

    filteredReports: (state) => {
      const q = String(state.query || "").trim().toLowerCase();
      const testerFilter = String(state.selectedTester || "").trim();
      if (!q && !testerFilter) return state.reports;
      return state.reports.filter((item) => {
        const tester = String(item?.tester || "").trim();
        if (testerFilter && tester !== testerFilter) {
          return false;
        }
        if (!q) {
          return true;
        }
        const id = String(item?.run_id || "").toLowerCase();
        const summary = String(item?.summary || "").toLowerCase();
        const note = String(item?.run_note || "").toLowerCase();
        return id.includes(q) || summary.includes(q) || note.includes(q);
      });
    },
  },

  actions: {
    async fetchReports() {
      if (this.refreshInFlight) return;
      this.refreshInFlight = true;
      try {
        this.reports = await fetchReportsList();
      } catch (_error) {
        this.reports = [];
      } finally {
        this.refreshInFlight = false;
      }
    },

    setQuery(value) {
      this.query = value;
    },

    setTester(value) {
      this.selectedTester = value;
    },

    startAutoRefresh() {
      this.stopAutoRefresh();
      this.refreshTimer = window.setInterval(() => {
        void this.fetchReports();
      }, REPORTS_REFRESH_INTERVAL_MS);
    },

    stopAutoRefresh() {
      if (this.refreshTimer) {
        window.clearInterval(this.refreshTimer);
        this.refreshTimer = null;
      }
    },
  },
});
