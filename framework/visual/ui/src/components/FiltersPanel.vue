<template>
  <div class="card mb-3 shadow-sm">
    <div class="card-body">
      <div class="row g-2 align-items-end">
        <div class="col-12 col-md-4">
          <label class="form-label">Szukaj (scenario/message)</label>
          <input class="form-control" v-model="store.q" placeholder="np. hero, header..." />
        </div>

        <div class="col-6 col-md-2">
          <label class="form-label">Status</label>
          <select class="form-select" v-model="store.status">
            <option value="">All</option>
            <option value="passed">passed</option>
            <option value="failed">failed</option>
            <option value="skipped">skipped</option>
            <option value="error">error</option>
            <option value="new">new</option>
          </select>
        </div>

        <div class="col-6 col-md-2">
          <label class="form-label">Mode</label>
          <select class="form-select" v-model="store.mode">
            <option value="">All</option>
            <option value="pixel">pixel</option>
            <option value="perceptual">perceptual</option>
            <option value="hybrid">hybrid</option>
          </select>
        </div>

        <div class="col-6 col-md-2">
          <label class="form-label">Sort</label>
          <select class="form-select" v-model="store.sortKey">
            <option value="scenario_id">scenario_id</option>
            <option value="status">status</option>
            <option value="pixel_changed_ratio">pixel</option>
            <option value="lpips">lpips</option>
            <option value="dists">dists</option>
          </select>
        </div>

        <div class="col-6 col-md-2">
          <label class="form-label">&nbsp;</label>
          <button class="btn btn-outline-secondary w-100" @click="$emit('reset')">Reset</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "FiltersPanel",
  props: {
    store: {
      type: Object,
      required: true,
    },
  },
};
</script>
