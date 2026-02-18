<template>
  <div class="card shadow-sm mb-3">
    <div class="card-body py-3">
      <label class="form-label mb-1 small text-muted">{{ t('filters.searchLabel') }}</label>
      <input
        :value="modelValue"
        class="form-control"
        type="text"
        :placeholder="t('filters.searchPlaceholder')"
        @input="$emit('update:modelValue', $event.target.value)"
      />
    </div>
  </div>
</template>

<script>
import { t } from "../../lib/i18n";

export default {
  name: "ReportsFilters",
  props: {
    modelValue: {
      type: String,
      default: "",
    },
  },
  emits: ["update:modelValue"],
  setup() {
    return { t };
  },
};
</script>

<style scoped>
.card {
  background-color: var(--card-bg);
  border-color: var(--border);
}
</style>
