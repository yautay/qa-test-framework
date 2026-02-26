<template>
  <section class="report-header mb-3 p-4 rounded-4">
    <div class="d-flex align-items-center justify-content-between">
      <div>
        <h3 class="mb-0">{{ t('report.title') }}</h3>
        <div class="text-muted small">{{ t('report.run') }}: <span class="mono">{{ runId || "unknown" }}</span></div>
      </div>
      <div class="d-flex align-items-center gap-2">
        <div class="d-flex align-items-center gap-2 report-actions" role="group" aria-label="tag persistence">
          <button type="button" class="btn btn-success btn-sm" :class="{ 'btn-saturated': store.baselineCandidates.length > 0 }" @click="$emit('send-baseline')" :disabled="store.baselineCandidates.length === 0">
            {{ t('report.sendBaseline') }}
          </button>
          <button type="button" class="btn btn-primary btn-sm" :class="{ 'btn-saturated': store.reportCandidatesCount > 0 || pdfGenerated }" @click="$emit('send-report')" :disabled="!runId">
            {{ t('report.sendReport') }}
          </button>
        </div>
        <div class="text-muted small mono">{{ summaryText }}</div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { t } from "../lib/i18n";

const props = defineProps({
  runId: {
    type: String,
    default: "",
  },
  store: {
    type: Object,
    required: true,
  },
  pdfGenerated: {
    type: Boolean,
    default: false,
  },
});

defineEmits(["send-baseline", "send-report"]);

const summaryText = computed(() => {
  const summary = props.store?.summary || {};
  const total = Number(summary.total || 0);
  const passed = Number(summary.passed || 0);
  const failed = Number(summary.failed || 0);
  const skipped = Number(summary.skipped || 0);
  const uncertain = Number(summary.uncertain || 0);
  const parts = [
    `${t("report.summary.total")}: ${total}`,
    `${t("report.summary.passed")}: ${passed}`,
    `${t("report.summary.failed")}: ${failed}`,
    `${t("report.summary.skipped")}: ${skipped}`,
  ];
  if (uncertain > 0) {
    parts.push(`${t("report.summary.uncertain")}: ${uncertain}`);
  }
  return parts.join(" | ");
});
</script>

<style scoped>
.report-header {
  background: var(--hero-gradient);
  border: 1px solid var(--border);
}
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.btn-saturated {
  filter: saturate(1.4);
}
</style>
