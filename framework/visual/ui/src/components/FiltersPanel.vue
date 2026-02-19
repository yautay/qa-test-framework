<template>
  <div class="card mb-3 shadow-sm">
    <div class="card-body">
      <div class="row g-2 align-items-end">
        <div class="col-12 col-md-4">
          <label class="form-label">{{ t('filtersPanel.search') }}</label>
          <input class="form-control" v-model="store.q" :placeholder="t('filtersPanel.searchPlaceholder')" />
        </div>

        <div class="col-6 col-md-2">
          <label class="form-label">{{ t('filtersPanel.status') }}</label>
          <select class="form-select" v-model="store.status">
            <option value="">{{ t('filtersPanel.all') }}</option>
            <option value="passed">{{ t('status.passed') }}</option>
            <option value="failed">{{ t('status.failed') }}</option>
            <option value="skipped">{{ t('status.skipped') }}</option>
          </select>
        </div>

        <div class="col-6 col-md-2">
          <label class="form-label">{{ t('filtersPanel.sort') }}</label>
          <select class="form-select" v-model="store.sortKey">
            <option value="scenario_id">{{ t('sort.scenario_id') }}</option>
            <option value="status">{{ t('sort.status') }}</option>
            <option value="pixel_changed_ratio">{{ t('sort.pixel') }}</option>
            <option value="lpips">{{ t('sort.lpips') }}</option>
            <option value="dists">{{ t('sort.dists') }}</option>
            <option value="tags">{{ t('sort.tags') }}</option>
          </select>
        </div>

        <div class="col-6 col-md-2">
          <label class="form-label">&nbsp;</label>
          <button class="btn btn-outline-secondary w-100" @click="$emit('reset')">{{ t('filtersPanel.reset') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { t } from "../lib/i18n";

export default {
  name: "FiltersPanel",
  props: {
    store: {
      type: Object,
      required: true,
    },
  },
  emits: ["reset"],
  methods: {
    t(key) {
      return t(key);
    },
  },
};
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
