<template>
  <header class="hero-header mb-3 p-4 rounded-4">
    <div class="d-flex flex-wrap justify-content-between align-items-end gap-3">
      <div>
        <div class="eyebrow">Visual Reports</div>
        <h1 class="mb-1">{{ t('hero.title') }}</h1>
        <p class="mb-0 text-muted">{{ t('hero.subtitle') }}</p>
      </div>
      <div class="d-flex align-items-center gap-3">
        <div class="stats-pill">
          <span class="stats-label">{{ t('hero.availableRuns') }}</span>
          <span class="stats-value">{{ total }}</span>
        </div>
        <select
          class="form-select form-select-sm theme-select"
          :value="currentTheme"
          @change="setTheme($event.target.value)"
        >
          <option v-for="(preset, key) in presets" :key="key" :value="key">
            {{ preset.name }}
          </option>
        </select>
        <div class="btn-group btn-group-sm language-selector" role="group">
          <button
            type="button"
            class="btn"
            :class="locale === 'en' ? 'btn-primary' : 'btn-outline-primary'"
            @click="setLocale('en')"
          >
            EN
          </button>
          <button
            type="button"
            class="btn"
            :class="locale === 'pl' ? 'btn-primary' : 'btn-outline-primary'"
            @click="setLocale('pl')"
          >
            PL
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
import { t, locale, setLocale } from "../../lib/i18n";
import { currentTheme, setTheme, presets } from "../../lib/themes";

export default {
  name: "HeroHeader",
  props: {
    total: {
      type: Number,
      default: 0,
    },
  },
  setup() {
    return { t, locale, setLocale, currentTheme, setTheme, presets };
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

.theme-select {
  width: auto;
  min-width: 140px;
}
</style>
