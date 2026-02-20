<template>
  <div class="card shadow-sm">
    <div class="card-body py-5 text-center text-muted">
      <div class="mb-2">{{ t('empty.noReports') }}</div>
      <div class="small">{{ t('empty.runCommand') }}</div>
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
