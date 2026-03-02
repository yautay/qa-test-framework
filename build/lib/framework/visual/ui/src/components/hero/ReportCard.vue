<template>
  <article class="card h-100 shadow-sm report-card">
    <div class="card-body d-flex flex-column gap-2">
      <div class="d-flex justify-content-between align-items-center gap-2">
        <div class="mono fw-semibold run-id">{{ report.run_id }}</div>
        <div class="d-flex gap-1">
          <span v-if="showPmsPending" class="badge bg-secondary pms-signal" :title="pmsPendingTitle">⏳</span>
          <span v-if="showPmsError" class="badge bg-warning text-dark pms-signal" :title="pmsErrorTitle">⚠</span>
          <span v-if="showPmsSuccess" class="badge bg-success pms-signal" :title="pmsSuccessTitle">✅</span>
          <span v-if="showSyncWarning" class="badge bg-warning text-dark sync-warning-icon" :title="syncWarningTitle">⚠</span>
          <span class="badge text-bg-secondary">{{ report.total || 0 }} {{ t('card.tests') }}</span>
        </div>
      </div>

      <div class="text-muted small">{{ report.updated_at || "unknown" }}</div>

      <div v-if="report.tester" class="text-muted small">
        <span class="meta-label">{{ t('card.tester') }}:</span> {{ report.tester }}
      </div>

      <div v-if="report.run_note" class="text-muted small run-note">
        <span class="meta-label">{{ t('card.runNote') }}:</span> {{ report.run_note }}
      </div>

      <div data-name="build-info" class="d-flex flex-wrap gap-2 small">
        <span class="badge text-bg-success">{{ report.passed || 0 }}</span>
        <span class="badge text-bg-danger">{{ report.failed || 0 }}</span>
        <span v-if="report.uncertain" class="badge text-bg-warning">{{ report.uncertain }}</span>
        <span v-if="report.skipped" class="badge text-bg-secondary">{{ report.skipped }}</span>
        
        <div class="ms-auto d-flex gap-1">
          <span v-if="report.bug_count" class="badge bg-danger" :title="t('tags.bug')">
            {{ report.bug_count }}
          </span>
          <span v-if="report.aso_count" class="badge bg-warning text-dark" :title="t('tags.aso')">
            {{ report.aso_count }}
          </span>
        </div>
      </div>

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
    hasSyncErrors: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    reportUrl() {
      return reportPath(this.report?.run_id || "");
    },
    showSyncWarning() {
      return !!(this.hasSyncErrors || this.report?.has_sync_issues);
    },
    pmsPendingCount() {
      return Number(this.report?.pms_pending_count || 0);
    },
    pmsErrorCount() {
      return Number(this.report?.pms_error_count || 0);
    },
    pmsSuccessCount() {
      return Number(this.report?.pms_success_count || this.report?.pms_done_count || 0);
    },
    showPmsPending() {
      return this.pmsPendingCount > 0;
    },
    showPmsError() {
      return this.pmsErrorCount > 0;
    },
    showPmsSuccess() {
      return this.pmsSuccessCount > 0;
    },
    pmsPendingTitle() {
      return `${t("pms.pendingBuild")}: ${this.pmsPendingCount}`;
    },
    pmsErrorTitle() {
      return `${t("pms.errorBuild")}: ${this.pmsErrorCount}`;
    },
    pmsSuccessTitle() {
      return `${t("pms.successBuild")}: ${this.pmsSuccessCount}`;
    },
    syncWarningTitle() {
      const base = t("sync.buildHasErrors");
      const failed = Number(this.report?.sync_failed_count || 0);
      const pending = Number(this.report?.sync_pending_count || 0);
      const sending = Number(this.report?.sync_sending_count || 0);
      const unsynced = Number(this.report?.sync_unsynced_count || 0);
      const counters = [
        `${t("sync.failedCount")}: ${failed}`,
        `${t("sync.pendingCount")}: ${pending}`,
        `${t("sync.sendingCount")}: ${sending}`,
        `${t("sync.unsyncedCount")}: ${unsynced}`,
      ].join(", ");
      return `${base}: ${counters}`;
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

.run-id {
  color: var(--run-id-color, var(--body-color));
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

.pms-signal,
.sync-warning-icon {
  min-width: 1.5rem;
  text-align: center;
}
</style>
