<template>
  <header class="app-header mb-3 p-3 rounded-4">
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-3">
      <div class="d-flex align-items-center gap-3">
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
            title="English"
          >
            🇬🇧
          </button>
          <button
            type="button"
            class="btn"
            :class="locale === 'pl' ? 'btn-primary' : 'btn-outline-primary'"
            @click="setLocale('pl')"
            title="Polski"
          >
            🇵🇱
          </button>
        </div>
      </div>
      <div class="datetime text-muted small mono">
        {{ formattedDateTime }}
      </div>
    </div>
  </header>
</template>

<script>
import { ref, onMounted, onUnmounted } from "vue";
import { locale, setLocale } from "../lib/i18n";
import { currentTheme, setTheme, presets } from "../lib/themes";

export default {
  name: "AppHeader",
  setup() {
    const formattedDateTime = ref("");

    const updateDateTime = () => {
      const now = new Date();
      const options = {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: "Europe/Warsaw",
      };
      formattedDateTime.value = now.toLocaleString("pl-PL", options);
    };

    let intervalId = null;

    onMounted(() => {
      updateDateTime();
      intervalId = setInterval(updateDateTime, 60000);
    });

    onUnmounted(() => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    });

    return {
      locale,
      setLocale,
      currentTheme,
      setTheme,
      presets,
      formattedDateTime,
    };
  },
};
</script>

<style scoped>
.app-header {
  background: var(--card-bg);
  border: 1px solid var(--border);
}

.theme-select {
  width: auto;
  min-width: 140px;
}

.datetime {
  min-width: 140px;
  text-align: right;
}
</style>
