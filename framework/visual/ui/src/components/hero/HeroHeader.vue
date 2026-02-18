<template>
  <header class="hero-header mb-3 p-4 rounded-4">
    <div class="d-flex flex-wrap justify-content-between align-items-end gap-3">
      <div>
        <div class="eyebrow">Visual Reports</div>
        <h1 class="mb-1">{{ t('hero.title') }}</h1>
        <p class="mb-0 text-muted">{{ t('hero.subtitle') }}</p>
      </div>
      <div class="stats-pill">
        <span class="stats-label">{{ t('hero.availableRuns') }}</span>
        <span class="stats-value">{{ total }}</span>
      </div>
    </div>
  </header>
</template>

<script>
import { t } from "../../lib/i18n";

export default {
  name: "HeroHeader",
  props: {
    total: {
      type: Number,
      default: 0,
    },
  },
  setup() {
    return { t };
  },
};
</script>

<style scoped>
.hero-header {
  background: var(--hero-gradient);
  border: 1px solid var(--border);
}

.eyebrow {
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.75rem;
  color: var(--primary);
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
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.5rem 1rem;
}

.stats-label {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.stats-value {
  font-weight: 700;
  font-size: 1.1rem;
}
</style>
