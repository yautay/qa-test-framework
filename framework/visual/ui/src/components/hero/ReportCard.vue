<template>
  <article class="card h-100 shadow-sm report-card">
    <div class="card-body d-flex flex-column gap-2">
      <div class="d-flex justify-content-between align-items-center gap-2">
        <div class="mono fw-semibold">{{ report.run_id }}</div>
        <span class="badge text-bg-secondary">{{ report.total || 0 }} tests</span>
      </div>

      <div class="text-muted small">{{ report.updated_at || "unknown" }}</div>

      <div class="d-flex flex-wrap gap-2 small">
        <span class="badge bg-success-subtle text-success-emphasis">passed {{ report.passed || 0 }}</span>
        <span class="badge bg-danger-subtle text-danger-emphasis">failed {{ report.failed || 0 }}</span>
        <span class="badge bg-warning-subtle text-warning-emphasis">new {{ report.new || 0 }}</span>
      </div>

      <div class="text-muted small flex-grow-1">{{ report.summary || "No summary available" }}</div>

      <a :href="reportUrl" class="btn btn-primary btn-sm mt-2">Open report</a>
    </div>
  </article>
</template>

<script>
import { reportPath } from "../../lib/runtimeRoute";

export default {
  name: "ReportCard",
  props: {
    report: {
      type: Object,
      required: true,
    },
  },
  computed: {
    reportUrl() {
      return reportPath(this.report?.run_id || "");
    },
  },
};
</script>

<style scoped>
.report-card {
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
</style>
