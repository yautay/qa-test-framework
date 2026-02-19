<template>
  <article class="card h-100 shadow-sm report-card">
    <div class="card-body d-flex flex-column gap-2">
      <div class="d-flex justify-content-between align-items-center gap-2">
        <div class="mono fw-semibold">{{ report.run_id }}</div>
        <span class="badge text-bg-secondary">{{ report.total || 0 }} {{ t('card.tests') }}</span>
      </div>

      <div class="text-muted small">{{ report.updated_at || "unknown" }}</div>

      <div v-if="report.tester" class="text-muted small">
        <span class="meta-label">{{ t('card.tester') }}:</span> {{ report.tester }}
      </div>

      <div v-if="report.run_note" class="text-muted small run-note">
        <span class="meta-label">{{ t('card.runNote') }}:</span> {{ report.run_note }}
      </div>

      <div class="d-flex flex-wrap gap-2 small">
        <span class="badge bg-success-subtle text-success-emphasis">{{ t('card.passed') }} {{ report.passed || 0 }}</span>
        <span class="badge bg-danger-subtle text-danger-emphasis">{{ t('card.failed') }} {{ report.failed || 0 }}</span>
      </div>

      <div class="text-muted small flex-grow-1">{{ report.summary || "No summary available" }}</div>

      <a :href="reportUrl" class="btn btn-primary btn-sm mt-2" @click="navigateToReport">{{ t('card.openReport') }}</a>
    </div>
  </article>
</template>

<script>
import { reportPath } from "../../lib/runtimeRoute";
import { t } from "../../lib/i18n";

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
  methods: {
    navigateToReport(evt) {
      evt.preventDefault();
      window.history.pushState(null, "", this.reportUrl);
      window.dispatchEvent(new PopStateEvent("popstate"));
    },
  },
  setup() {
    return { t };
  },
};
</script>

<style scoped>
.report-card {
  background-color: var(--card-bg);
  border: 1px solid var(--border);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.meta-label {
  font-weight: 600;
}

.run-note {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
