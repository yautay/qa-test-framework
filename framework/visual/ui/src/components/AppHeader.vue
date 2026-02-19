<template>
  <header class="app-header mb-3 p-3 rounded-4">
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-3">
      <div class="d-flex align-items-center gap-3">
        <div class="theme-dropdown dropdown">
          <button
            class="btn btn-theme dropdown-toggle"
            type="button"
            data-bs-toggle="dropdown"
            aria-expanded="false"
          >
            <span
              class="theme-gradient-preview"
              :style="{ background: currentPreset?.dropdownGradient }"
            ></span>
            <span class="theme-name">{{ currentPreset?.name }}</span>
          </button>
          <ul class="dropdown-menu dropdown-menu-end">
            <li v-for="(preset, key) in presets" :key="key">
              <button
                class="dropdown-item"
                :class="{ active: key === currentTheme }"
                type="button"
                @click="setTheme(key)"
              >
                <span
                  class="theme-gradient-preview"
                  :style="{ background: preset.dropdownGradient }"
                ></span>
                <span>{{ preset.name }}</span>
              </button>
            </li>
          </ul>
        </div>
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
import { ref, onMounted, onUnmounted, computed } from "vue";
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
      currentPreset: computed(() => presets[currentTheme.value]),
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

.theme-dropdown .btn-theme {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  min-width: 140px;
  background-color: var(--card-bg);
  border: 1px solid var(--border);
  color: var(--body-color);
  font-size: 0.875rem;
}

.theme-dropdown .btn-theme:hover {
  border-color: var(--primary);
}

.theme-dropdown .btn-theme::after {
  margin-left: auto;
}

.theme-gradient-preview {
  display: inline-block;
  width: 24px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.theme-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.theme-dropdown .dropdown-menu {
  background-color: var(--card-bg);
  border-color: var(--border);
  min-width: 180px;
}

.theme-dropdown .dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--body-color);
  padding: 8px 12px;
}

.theme-dropdown .dropdown-item:hover {
  background-color: var(--body-bg);
}

.theme-dropdown .dropdown-item.active {
  background-color: var(--primary);
  color: #fff;
}

.datetime {
  min-width: 140px;
  text-align: right;
}

.language-selector .btn {
  background-color: var(--card-bg);
  border-color: var(--border);
  color: var(--body-color);
}

.language-selector .btn:hover {
  background-color: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

.language-selector .btn.btn-primary,
.language-selector .btn.active {
  background-color: var(--primary);
  border-color: var(--primary);
  color: #fff;
}
</style>
