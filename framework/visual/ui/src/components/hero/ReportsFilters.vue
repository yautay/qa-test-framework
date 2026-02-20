<template>
  <div class="card shadow-sm mb-3">
    <div class="card-body py-3">
      <div class="row g-2">
        <div class="col-12 col-md-8">
          <label class="form-label mb-1 small text-muted">{{ t('filters.searchLabel') }}</label>
          <input
            :value="store.query"
            class="form-control"
            type="text"
            :placeholder="t('filters.searchPlaceholder')"
            @input="store.setQuery($event.target.value)"
          />
        </div>
        <div class="col-12 col-md-4">
          <label class="form-label mb-1 small text-muted">{{ t('filters.testerLabel') }}</label>
          <select
            :value="store.selectedTester"
            class="form-select"
            @change="store.setTester($event.target.value)"
          >
            <option value="">{{ t('filters.allTesters') }}</option>
            <option v-for="tester in store.testerOptions" :key="tester" :value="tester">{{ tester }}</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useReportsStore } from "../../stores/reportsStore";
import { t } from "../../lib/i18n";

const store = useReportsStore();
</script>

<style scoped>
.card {
  background-color: var(--card-bg);
  border-color: var(--border);
}

.form-control {
  background-color: var(--card-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.form-control::placeholder {
  color: var(--text-muted);
}

.form-control:focus {
  background-color: var(--card-bg);
  color: var(--body-color);
  border-color: var(--primary);
}

.form-select {
  background-color: var(--card-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.form-select:focus {
  background-color: var(--card-bg);
  color: var(--body-color);
  border-color: var(--primary);
}
</style>
