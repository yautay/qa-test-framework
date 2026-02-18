<template>
  <section class="hero-wrap">
    <AppHeader />
    <HeroHeader :total="filteredReports.length" />
    <ReportsFilters v-model="query" />
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
      reports: [],
    };
  },
  computed: {
    filteredReports() {
      const q = String(this.query || "").trim().toLowerCase();
      if (!q) return this.reports;
      return this.reports.filter((item) => {
        const id = String(item?.run_id || "").toLowerCase();
        const summary = String(item?.summary || "").toLowerCase();
        return id.includes(q) || summary.includes(q);
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
