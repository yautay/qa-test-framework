<template>
  <header class="app-header mb-3 p-3 rounded-4">
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-3">
      <div class="d-flex align-items-center gap-3">
        <div class="theme-dropdown dropdown">
          <button
            class="btn btn-theme dropdown-toggle"
            type="button"
            :aria-expanded="isOpen"
            @click="isOpen = !isOpen"
          >
            <span
              class="theme-gradient-preview"
              :style="{ background: currentPreset?.dropdownGradient }"
            ></span>
            <span class="theme-name">{{ currentPreset?.name }}</span>
          </button>
          <ul class="dropdown-menu dropdown-menu-end" :class="{ show: isOpen }">
            <li v-for="(preset, key) in presets" :key="key">
              <button
                class="dropdown-item"
                :class="{ active: key === currentTheme }"
                type="button"
                @click="selectTheme(key)"
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
            :title="t('language.english')"
          >
            🇬🇧
          </button>
          <button
            type="button"
            class="btn"
            :class="locale === 'pl' ? 'btn-primary' : 'btn-outline-primary'"
            @click="setLocale('pl')"
            :title="t('language.polish')"
          >
            🇵🇱
          </button>
          <button
            type="button"
            class="btn"
            :class="locale === 'uk' ? 'btn-primary' : 'btn-outline-primary'"
            @click="setLocale('uk')"
            :title="t('language.ukrainian')"
          >
            🇺🇦
          </button>
        </div>
      </div>
      <div class="datetime-wrap text-muted small mono">
        <span class="datetime">{{ formattedDateTime }}</span>
        <div class="app-info" tabindex="0" role="button" aria-label="Application build info">
          <span class="app-info-icon">i</span>
          <div class="app-info-tooltip" role="tooltip">
            <div class="app-info-row"><strong>Runtime</strong></div>
            <div class="app-info-row">version: {{ runtimeInfo.version }}</div>
            <div class="app-info-row">codename: {{ runtimeInfo.codename }}</div>
            <div class="app-info-row">commit: {{ runtimeInfo.commit }}</div>
            <div class="app-info-divider"></div>
            <div class="app-info-row"><strong>UI build</strong></div>
            <div class="app-info-row">version: {{ buildInfo.version }}</div>
            <div class="app-info-row">codename: {{ buildInfo.codename }}</div>
            <div class="app-info-row">commit: {{ buildInfo.commit }}</div>
            <div class="app-info-row">built at: {{ buildInfo.builtAt }}</div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { locale, setLocale, t } from "../lib/i18n";
import { currentTheme, setTheme, presets } from "../lib/themes";
import { fetchAppInfo } from "../lib/api/appInfoApi";

function normalizeText(value) {
  const text = String(value || "").trim();
  return text || "unknown";
}

function normalizeAppInfo(payload) {
  const runtime = payload?.runtime && typeof payload.runtime === "object" ? payload.runtime : {};
  const uiBuild = payload?.ui_build && typeof payload.ui_build === "object" ? payload.ui_build : {};
  return {
    runtimeInfo: {
      version: normalizeText(runtime.version),
      codename: normalizeText(runtime.codename),
      commit: normalizeText(runtime.commit),
    },
    buildInfo: {
      version: normalizeText(uiBuild.version),
      codename: normalizeText(uiBuild.codename),
      commit: normalizeText(uiBuild.commit),
      builtAt: normalizeText(uiBuild.built_at),
    },
  };
}

export default {
  name: "AppHeader",
  setup() {
    const formattedDateTime = ref("");
    const isOpen = ref(false);
    const runtimeInfo = ref({
      version: "loading...",
      codename: "loading...",
      commit: "loading...",
    });
    const buildInfo = ref({
      version: "loading...",
      codename: "loading...",
      commit: "loading...",
      builtAt: "loading...",
    });

    const selectTheme = (key) => {
      setTheme(key);
      isOpen.value = false;
    };

    const handleClickOutside = (event) => {
      if (!event.target.closest(".theme-dropdown")) {
        isOpen.value = false;
      }
    };

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

    const loadAppInfo = async () => {
      try {
        const payload = await fetchAppInfo();
        const normalized = normalizeAppInfo(payload);
        runtimeInfo.value = normalized.runtimeInfo;
        buildInfo.value = normalized.buildInfo;
      } catch (_error) {
        runtimeInfo.value = {
          version: "unknown",
          codename: "unknown",
          commit: "unknown",
        };
        buildInfo.value = {
          version: "unknown",
          codename: "unknown",
          commit: "unknown",
          builtAt: "unknown",
        };
      }
    };

    onMounted(() => {
      updateDateTime();
      intervalId = setInterval(updateDateTime, 60000);
      document.addEventListener("click", handleClickOutside);
      loadAppInfo();
    });

    onUnmounted(() => {
      if (intervalId) {
        clearInterval(intervalId);
      }
      document.removeEventListener("click", handleClickOutside);
    });

    return {
      locale,
      setLocale,
      t,
      currentTheme,
      currentPreset: computed(() => presets[currentTheme.value]),
      setTheme,
      presets,
      formattedDateTime,
      runtimeInfo,
      buildInfo,
      isOpen,
      selectTheme,
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
  display: none;
}

.theme-dropdown .dropdown-menu.show {
  display: block;
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
  min-width: 130px;
}

.datetime-wrap {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.app-info {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: 1px solid var(--border);
  border-radius: 50%;
  background: var(--card-bg);
  color: var(--text-muted);
  cursor: default;
  user-select: none;
  outline: none;
}

.app-info-icon {
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
}

.app-info-tooltip {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 240px;
  padding: 10px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.16);
  color: var(--body-color);
  font-size: 12px;
  text-align: left;
  z-index: 30;
  opacity: 0;
  visibility: hidden;
  transform: translateY(4px);
  transition: opacity 0.18s ease, transform 0.18s ease, visibility 0.18s ease;
  pointer-events: none;
}

.app-info:hover .app-info-tooltip,
.app-info:focus .app-info-tooltip,
.app-info:focus-visible .app-info-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.app-info-row {
  line-height: 1.35;
}

.app-info-divider {
  height: 1px;
  margin: 6px 0;
  background: var(--border);
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
