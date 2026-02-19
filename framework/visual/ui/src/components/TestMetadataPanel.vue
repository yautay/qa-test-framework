<template>
  <div v-if="active" class="metadata-overlay" @click.self="$emit('close')">
    <div class="metadata-card">
      <div class="d-flex align-items-center justify-content-between mb-2">
        <h5 class="mb-0">{{ t('metadata.title') }}</h5>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="$emit('close')">
          {{ t('metadata.close') }}
        </button>
      </div>

      <div v-if="rows.length === 0" class="text-muted small">{{ t('metadata.empty') }}</div>
      <div v-else class="table-responsive">
        <table class="table table-sm align-middle mb-0">
          <thead>
            <tr>
              <th>{{ t('metadata.key') }}</th>
              <th>{{ t('metadata.value') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.key">
              <td class="mono small">{{ row.key }}</td>
              <td class="small">{{ row.value }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { t } from "../lib/i18n";

function flattenMetadata(input, prefix = "") {
  if (!input || typeof input !== "object") return [];
  const out = [];
  for (const [rawKey, rawValue] of Object.entries(input)) {
    const key = prefix ? `${prefix}.${rawKey}` : rawKey;
    if (rawValue && typeof rawValue === "object" && !Array.isArray(rawValue)) {
      out.push(...flattenMetadata(rawValue, key));
      continue;
    }
    const value = Array.isArray(rawValue) ? rawValue.join(", ") : rawValue;
    out.push({
      key,
      value: value === undefined || value === null || value === "" ? "-" : String(value),
    });
  }
  return out;
}

export default {
  name: "TestMetadataPanel",
  props: {
    active: {
      type: Boolean,
      default: false,
    },
    metadata: {
      type: Object,
      default: () => ({}),
    },
  },
  emits: ["close"],
  computed: {
    rows() {
      return flattenMetadata(this.metadata || {});
    },
  },
  methods: {
    t(key) {
      return t(key);
    },
  },
};
</script>

<style scoped>
.metadata-overlay {
  position: fixed;
  inset: 0;
  z-index: 1080;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.metadata-card {
  width: min(920px, 100%);
  max-height: 85vh;
  overflow: auto;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  padding: 1rem;
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.2);
}

.table {
  --bs-table-bg: var(--card-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.table thead th,
.table tbody td {
  background-color: var(--card-bg);
  color: var(--body-color);
  border-color: var(--border);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
</style>
