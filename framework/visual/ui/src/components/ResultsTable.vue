<template>
  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th>{{ t('listing.scenario') }}</th>
            <th class="small-col">{{ t('listing.status') }}</th>
            <th class="small-col">{{ t('listing.pixel') }}</th>
            <th class="small-col">{{ t('listing.lpips') }}</th>
            <th class="small-col">{{ t('listing.dists') }}</th>
            <th>{{ t('listing.message') }}</th>
            <th class="small-col">{{ t('listing.viewport') }}</th>
            <th class="small-col">{{ t('listing.browser') }}</th>
            <th class="small-col text-end">{{ t('listing.metadata') }}</th>
            <th>{{ t('listing.artifacts') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, index) in rows" :key="rowKey(r, index)" 
              :class="{ 'table-active': index === selectedIndex }"
              @click="$emit('select', index)"
              @dblclick="$emit('show', r, 'test', index)">
            <td class="mono">
              <span>{{ r.scenario_id }}</span>
            </td>

            <td class="small-col">
              <span class="badge"
                :class="statusClass(r.status)">{{ r.status }}</span>
            </td>

            <td class="small-col mono">{{ fmt(r.pixel_changed_ratio) }}</td>
            <td class="small-col mono">{{ fmt(r.lpips) }}</td>
            <td class="small-col mono">{{ fmt(r.dists) }}</td>
            <td style="max-width: 420px;">
              <div class="d-flex flex-wrap gap-1 mb-1">
                <span v-if="rowHasSyncError(r)" 
                      class="badge bg-warning text-dark sync-error-icon" 
                      :title="getSyncErrorMessage(r)">
                  ⚠
                </span>
                <span v-if="rowHasTag(r, 'bug')" class="badge bg-danger">{{ t('tags.bug') }}</span>
                <span v-if="rowHasTag(r, 'aso')" class="badge bg-warning text-dark">{{ t('tags.aso') }}</span>
                <span v-if="rowHasTag(r, 'baseline')" class="badge bg-success">{{ t('tags.baseline') }}</span>
                <span v-if="rowHasTag(r, 'bug_reported')" class="badge bg-secondary">{{ t('tags.bugSent') }}</span>
                <span v-if="rowHasTag(r, 'aso_reported')" class="badge bg-secondary">{{ t('tags.asoSent') }}</span>
                <span v-if="rowHasTag(r, 'note_reported')" class="badge bg-secondary">{{ t('tags.noteSent') }}</span>
                <button
                  v-if="rowHasNote(r)"
                  type="button"
                  class="badge note-badge"
                  @click.stop="$emit('open-note', r, index)"
                >
                  {{ t('tags.note') }}
                </button>
              </div>
              <div>{{ r.message || '' }}</div>
            </td>

            <td class="small-col">
              <span v-if="r.viewport"
                class="badge badge-viewport"
                :style="badgeStyle('viewport', r.viewport)"
              >
                {{ r.viewport }}
              </span>
            </td>

            <td class="small-col">
              <span v-if="r.browser"
                class="badge badge-browser"
                :style="badgeStyle('browser', r.browser)"
              >
                {{ r.browser }}
              </span>
            </td>

            <td class="small-col text-end">
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary metadata-icon"
                :title="t('metadata.open')"
                @click.stop="$emit('open-metadata', r, index)"
              >
                i
              </button>
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
            <td colspan="10" class="text-center text-muted py-4">{{ t('listing.noResults') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { t } from "../lib/i18n";
import { badgeStyle as computeBadgeStyle } from "../lib/badgeStyle";
import { statusBadgeClass } from "../lib/statusClass";

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
    syncErrors: {
      type: Object,
      default: () => ({}),
    },
  },
  emits: ["show", "select", "open-note", "open-metadata"],
  methods: {
    t(key) {
      return t(key);
    },
    statusClass(status) {
      return statusBadgeClass(status);
    },
    rowHasTag(row, tag) {
      const key = this.tagKeyForRow(row);
      const tags = this.tagLog?.[key];
      if (!tags) return false;
      if (tag === "bug") return !!tags.bug?.locked;
      if (tag === "aso") return !!tags.aso?.locked;
      if (tag === "baseline") return !!tags.baseline;
      if (tag === "bug_reported") return !!tags.bug?.synced;
      if (tag === "aso_reported") return !!tags.aso?.synced;
      if (tag === "note_reported") return !!tags.note?.synced;
      return false;
    },
    rowHasNote(row) {
      const key = this.tagKeyForRow(row);
      const noteText = this.tagLog?.[key]?.note?.content;
      return typeof noteText === "string" && !!noteText.trim();
    },
    rowKey(row, index) {
      const key = this.tagKeyForRow(row);
      if (key) return key;
      return `${row?.scenario_id || "row"}::${row?.viewport || ""}::${row?.browser || ""}::${index}`;
    },
    badgeStyle(type, value) {
      return computeBadgeStyle(type, value);
    },
    rowHasSyncError(row) {
      const key = this.tagKeyForRow(row);
      return !!this.syncErrors?.[key];
    },
    getSyncErrorMessage(row) {
      const key = this.tagKeyForRow(row);
      const error = this.syncErrors?.[key];
      return error?.message || "";
    },
  },
};
</script>

<style scoped>
.card {
  background-color: var(--card-bg);
  border-color: var(--border);
}

.table {
  --bs-table-bg: var(--card-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.table thead th {
  background-color: var(--body-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.table tbody td {
  background-color: var(--card-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.table tbody tr:hover td {
  background-color: var(--body-bg);
}

.table-light {
  --bs-table-bg: var(--body-bg);
  color: var(--body-color);
}

.small-col {
  white-space: nowrap;
}

.artifact-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 0.25rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.badge-viewport,
.badge-browser {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
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

.note-badge {
  border: 1px solid var(--primary);
  background: var(--filter-highlight-bg, rgba(13, 110, 253, 0.12));
  color: var(--body-color);
  cursor: pointer;
}

.note-badge:hover {
  border-color: var(--filter-highlight-border, var(--primary));
}

.sync-error-icon {
  cursor: help;
}

.metadata-icon {
  width: 1.8rem;
  height: 1.8rem;
  border-radius: 999px;
  padding: 0;
  font-weight: 700;
  line-height: 1;
}
</style>
