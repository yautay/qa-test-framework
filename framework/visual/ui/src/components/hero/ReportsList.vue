<template>
  <div>
    <ReportsEmptyState v-if="reports.length === 0" />
    <div v-else class="row g-3">
      <div v-for="report in reports" :key="report.run_id" class="col-12 col-md-6 col-xl-4">
        <ReportCard :report="report" :has-sync-errors="hasSyncErrors(report.run_id)" />
      </div>
    </div>
  </div>
</template>

<script>
import ReportCard from "./ReportCard.vue";
import ReportsEmptyState from "./ReportsEmptyState.vue";
import { useReportsStore } from "../../stores/reportsStore";

export default {
  name: "ReportsList",
  components: {
    ReportCard,
    ReportsEmptyState,
  },
  props: {
    reports: {
      type: Array,
      default: () => [],
    },
  },
  setup() {
    const reportsStore = useReportsStore();
    const hasSyncErrors = (runId) => reportsStore.hasReportSyncErrors(runId);
    return { hasSyncErrors };
  },
};
</script>
