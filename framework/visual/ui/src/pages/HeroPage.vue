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
  async mounted() {
    try {
      this.reports = await fetchReportsList();
    } catch (_error) {
      this.reports = [];
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
