<template>
  <header class="hero-header mb-3 p-4 rounded-4">
    <div class="d-flex flex-wrap justify-content-between align-items-end gap-3">
      <div>
        <div class="eyebrow">Visual Reports</div>
        <h1 class="mb-1">Artifacts Dashboard</h1>
        <p class="mb-0 text-muted">Wybierz raport visual i przejdz do listy testow.</p>
      </div>
      <div class="stats-pill">
        <span class="stats-label">Available runs</span>
        <span class="stats-value">{{ total }}</span>
      </div>
    </div>
  </header>
</template>

<script>
export default {
  name: "HeroHeader",
  props: {
    total: {
      type: Number,
      default: 0,
    },
  },
};
</script>

<style scoped>
.hero-header {
  background: linear-gradient(135deg, #f3f9ff 0%, #e8f5e9 100%);
  border: 1px solid rgba(13, 110, 253, 0.16);
}

.eyebrow {
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.75rem;
  color: #0d6efd;
  margin-bottom: 0.25rem;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
}

.stats-pill {
  display: inline-flex;
  align-items: baseline;
  gap: 0.5rem;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 999px;
  padding: 0.5rem 1rem;
}

.stats-label {
  color: #6c757d;
  font-size: 0.85rem;
}

.stats-value {
  font-weight: 700;
  font-size: 1.1rem;
}
</style>
