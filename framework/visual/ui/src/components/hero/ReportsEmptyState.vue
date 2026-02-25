<template>
  <div class="card shadow-sm empty-state-card">
    <div class="card-body py-5 text-center empty-state-body">
      <div class="mb-2 empty-state-text">{{ t('empty.noReports') }}</div>
      <div class="small empty-state-text">{{ t('empty.runCommand') }}</div>
    </div>
  </div>
</template>

<script>
import { t } from "../../lib/i18n";

export default {
  name: "ReportsEmptyState",
  setup() {
    return { t };
  },
};
</script>

<style scoped>
.empty-state-card {
  background-color: var(--card-bg);
  border-color: var(--border);
}

.empty-state-body {
  background-color: var(--card-bg);
  color: var(--body-color);
}

.empty-state-text {
  color: var(--text-muted);
}
</style>
