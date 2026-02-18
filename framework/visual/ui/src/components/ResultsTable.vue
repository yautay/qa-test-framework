<template>
  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th>{{ t('listing.scenario') }}</th>
            <th class="small-col">{{ t('listing.status') }}</th>
            <th class="small-col">{{ t('listing.mode') }}</th>
            <th class="small-col">{{ t('listing.pixel') }}</th>
            <th class="small-col">{{ t('listing.lpips') }}</th>
            <th class="small-col">{{ t('listing.dists') }}</th>
            <th>{{ t('listing.message') }}</th>
            <th>{{ t('listing.artifacts') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, index) in rows" :key="r.scenario_id" 
              :class="{ 'table-active': index === selectedIndex }"
              @click="$emit('select', index)"
              @dblclick="$emit('show', r, 'test', index)">
            <td class="mono">{{ r.scenario_id }}</td>

            <td class="small-col">
              <span class="badge"
                :class="statusClass(r.status)">{{ r.status }}</span>
            </td>

            <td class="small-col"><span class="badge text-bg-secondary">{{ r.compare_mode }}</span></td>
            <td class="small-col mono">{{ fmt(r.pixel_changed_ratio) }}</td>
            <td class="small-col mono">{{ fmt(r.lpips) }}</td>
            <td class="small-col mono">{{ fmt(r.dists) }}</td>
            <td style="max-width: 420px;">
              <div class="d-flex flex-wrap gap-1 mb-1">
                <span v-if="rowHasTag(r, 'bug')" class="badge bg-danger">{{ t('tags.bug') }}</span>
                <span v-if="rowHasTag(r, 'aso')" class="badge bg-warning text-dark">{{ t('tags.aso') }}</span>
                <span v-if="rowHasTag(r, 'baseline')" class="badge bg-success">{{ t('tags.baseline') }}</span>
              </div>
              <div>{{ r.message || '' }}</div>
            </td>

            <td style="min-width: 430px;">
              <div class="d-flex flex-wrap gap-2 artifact-icons">
                <span v-if="r.baseline_path" class="artifact-badge artifact-ref">{{ t('artifacts.ref') }}</span>
                <span v-if="r.actual_path" class="artifact-badge artifact-test">{{ t('artifacts.test') }}</span>
                <span v-if="r.diff_path" class="artifact-badge artifact-diff">{{ t('artifacts.diff') }}</span>
                <span v-if="r.heatmap_path" class="artifact-badge artifact-perc">{{ t('artifacts.lpips') }}</span>
              </div>
            </td>
          </tr>

          <tr v-if="rows.length===0">
            <td colspan="8" class="text-center text-muted py-4">{{ t('listing.noResults') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { t } from "../lib/i18n";

export default {
  name: "ResultsTable",
  props: {
    rows: {
      type: Array,
      default: () => [],
    },
    fmt: {
      type: Function,
      required: true,
    },
    tagLog: {
      type: Object,
      default: () => ({}),
    },
    tagKeyForRow: {
      type: Function,
      default: () => "",
    },
    selectedIndex: {
      type: Number,
      default: -1,
    },
  },
  emits: ["show", "select"],
  methods: {
    t(key) {
      return t(key);
    },
    statusClass(status) {
      if (status === 'passed') return 'text-bg-success';
      if (status === 'failed') return 'text-bg-danger';
      if (status === 'skipped' || status === 'new') return 'text-bg-warning';
      if (status === 'error') return 'text-bg-dark';
      return '';
    },
    rowHasTag(row, tag) {
      const key = this.tagKeyForRow(row);
      const tags = this.tagLog?.[key];
      return !!(tags && tags[tag]);
    },
  },
};
</script>

<style scoped>
.artifact-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 0.25rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.artifact-ref {
  background-color: var(--primary);
  color: white;
  opacity: 0.85;
}

.artifact-test {
  background-color: var(--success);
  color: white;
  opacity: 0.85;
}

.artifact-diff {
  background-color: var(--danger);
  color: white;
  opacity: 0.85;
}

.artifact-perc {
  background-color: var(--warning);
  color: #212529;
  opacity: 0.85;
}

.table-active {
  background-color: var(--body-bg) !important;
}
</style>
