<template>
  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th>Scenario</th>
            <th class="small-col">Status</th>
            <th class="small-col">Mode</th>
            <th class="small-col">Pixel</th>
            <th class="small-col">LPIPS</th>
            <th class="small-col">DISTS</th>
            <th>Message</th>
            <th>Artifacts</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, index) in rows" :key="r.scenario_id">
            <td class="mono">{{ r.scenario_id }}</td>

            <td class="small-col">
              <span class="badge"
                :class="statusClass(r.status)">{{ r.status }}</span>
            </td>

            <td class="small-col"><span class="badge text-bg-secondary">{{ r.compare_mode }}</span></td>
            <td class="small-col mono">{{ fmt(r.pixel_changed_ratio) }}</td>
            <td class="small-col mono">{{ fmt(r.lpips) }}</td>
            <td class="small-col mono">{{ fmt(r.dists) }}</td>
            <td style="max-width: 420px;">{{ r.message || '' }}</td>

            <td style="min-width: 430px;">
              <div class="d-flex flex-wrap gap-2">
                <button v-if="r.baseline_path" class="btn btn-sm btn-outline-primary" @click="$emit('show', r, 'ref', index)">ref</button>
                <button v-if="r.actual_path" class="btn btn-sm btn-outline-primary" @click="$emit('show', r, 'test', index)">test</button>
                <button v-if="r.diff_path" class="btn btn-sm btn-outline-primary" @click="$emit('show', r, 'diff', index)">pixel_diff</button>
                <button v-if="r.heatmap_path" class="btn btn-sm btn-outline-primary" @click="$emit('show', r, 'lpips', index)">lpips</button>
                <button v-if="r.baseline_path && r.actual_path" class="btn btn-sm btn-outline-success" @click="$emit('show', r, 'compare', index)">compare</button>
              </div>
            </td>
          </tr>

          <tr v-if="rows.length===0">
            <td colspan="8" class="text-center text-muted py-4">Brak wyników dla filtrów.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
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
  },
  methods: {
    statusClass(status) {
      if (status === 'passed') return 'text-bg-success';
      if (status === 'failed') return 'text-bg-danger';
      if (status === 'skipped' || status === 'new') return 'text-bg-warning';
      if (status === 'error') return 'text-bg-dark';
      return '';
    },
  },
};
</script>
