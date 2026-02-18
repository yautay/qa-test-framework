<template>
  <div class="card shadow-sm mb-3">
    <div class="card-body py-3">
      <label class="form-label mb-1 small text-muted">Search run id or summary</label>
      <input
        :value="modelValue"
        class="form-control"
        type="text"
        placeholder="e.g. 20260218"
        @input="$emit('update:modelValue', $event.target.value)"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: "ReportsFilters",
  props: {
    modelValue: {
      type: String,
      default: "",
    },
  },
  emits: ["update:modelValue"],
};
</script>
