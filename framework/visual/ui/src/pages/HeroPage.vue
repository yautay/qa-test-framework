<template>
  <section class="hero-wrap">
    <AppHeader />
    <HeroHeader :total="filteredReports.length" />
    <ReportsFilters
      :query-value="query"
      :tester-value="selectedTester"
      :testers="testerOptions"
      @update:query-value="query = $event"
      @update:tester-value="selectedTester = $event"
    />
    <ReportsList :reports="filteredReports" />
  </section>
</template>

<script>
import AppHeader from "../components/AppHeader.vue";
import HeroHeader from "../components/hero/HeroHeader.vue";
import ReportsFilters from "../components/hero/ReportsFilters.vue";
import ReportsList from "../components/hero/ReportsList.vue";
import { fetchReportsList } from "../lib/api/reportsApi";

const REPORTS_REFRESH_INTERVAL_MS = 5000;

export default {
  name: "HeroPage",
  components: {
    AppHeader,
    HeroHeader,
    ReportsFilters,
    ReportsList,
  },
  data() {
    return {
      query: "",
      selectedTester: "",
      reports: [],
      refreshTimer: null,
      refreshInFlight: false,
    };
  },
  computed: {
    testerOptions() {
      const unique = new Set();
      for (const item of this.reports) {
        const tester = String(item?.tester || "").trim();
        if (tester) unique.add(tester);
      }
      return Array.from(unique).sort((a, b) => a.localeCompare(b));
    },
    filteredReports() {
      const q = String(this.query || "").trim().toLowerCase();
      const testerFilter = String(this.selectedTester || "").trim();
      if (!q && !testerFilter) return this.reports;
      return this.reports.filter((item) => {
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
  methods: {
    async refreshReports() {
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
  },
  async mounted() {
    await this.refreshReports();
    this.refreshTimer = window.setInterval(() => {
      void this.refreshReports();
    }, REPORTS_REFRESH_INTERVAL_MS);
  },
  beforeUnmount() {
    if (this.refreshTimer) {
      window.clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  },
};
</script>

<style scoped>
.hero-wrap {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
