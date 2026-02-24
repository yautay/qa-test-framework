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
        <div
          class="perceptual-queue"
          :class="{ 'perceptual-queue--error': !!queueInfo.errorMessage }"
          :title="queueTooltip"
          aria-label="Perceptual queue stats"
        >
          <span class="perceptual-queue-label">PMS</span>
          <span class="perceptual-queue-value">{{ queueInfo.serverActive }}</span>
        </div>
        <div class="datetime-tooltip" tabindex="0" role="button" :aria-label="weekendCountdownText">
          <span class="datetime">{{ formattedDateTime }}</span>
          <div class="datetime-tooltip-content" role="tooltip">{{ weekendCountdownText }}</div>
        </div>
        <div class="app-info" tabindex="0" role="button" :aria-label="t('appInfo.ariaLabel')">
          <span class="app-info-icon">i</span>
          <div class="app-info-tooltip" role="tooltip">
            <div class="app-info-row"><strong>{{ t('appInfo.runtime') }}</strong></div>
            <div class="app-info-row">{{ t('appInfo.version') }}: {{ runtimeInfo.version }}</div>
            <div class="app-info-row">{{ t('appInfo.codename') }}: {{ runtimeInfo.codename }}</div>
            <div class="app-info-row">{{ t('appInfo.commit') }}: {{ runtimeInfo.commit }}</div>
            <div class="app-info-divider"></div>
            <div class="app-info-row"><strong>{{ t('appInfo.uiBuild') }}</strong></div>
            <div class="app-info-row">{{ t('appInfo.version') }}: {{ buildInfo.version }}</div>
            <div class="app-info-row">{{ t('appInfo.codename') }}: {{ buildInfo.codename }}</div>
            <div class="app-info-row">{{ t('appInfo.uiSrcVersion') }}: {{ buildInfo.uiSrcVersion }}</div>
            <div class="app-info-row">{{ t('appInfo.commit') }}: {{ buildInfo.commit }}</div>
            <div class="app-info-row">{{ t('appInfo.builtAt') }}: {{ buildInfo.builtAt }}</div>
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
import { fetchPerceptualQueue } from "../lib/api/perceptualApi";

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
      uiSrcVersion: normalizeText(uiBuild.ui_src_version),
      commit: normalizeText(uiBuild.commit),
      builtAt: normalizeText(uiBuild.built_at),
    },
  };
}

const WARSAW_TIME_ZONE = "Europe/Warsaw";

const warsawDateFormatter = new Intl.DateTimeFormat("pl-PL", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: WARSAW_TIME_ZONE,
});

const warsawTimeZoneFormatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: WARSAW_TIME_ZONE,
  timeZoneName: "short",
});

const warsawPartsFormatter = new Intl.DateTimeFormat("en-US", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
  weekday: "short",
  timeZone: WARSAW_TIME_ZONE,
});

const WEEKDAY_TO_INDEX = {
  Sun: 0,
  Mon: 1,
  Tue: 2,
  Wed: 3,
  Thu: 4,
  Fri: 5,
  Sat: 6,
};

function getWarsawParts(date) {
  const parts = warsawPartsFormatter.formatToParts(date);
  const mapped = {};
  for (const part of parts) {
    if (part.type !== "literal") {
      mapped[part.type] = part.value;
    }
  }
  return {
    year: Number(mapped.year),
    month: Number(mapped.month),
    day: Number(mapped.day),
    hour: Number(mapped.hour),
    minute: Number(mapped.minute),
    second: Number(mapped.second),
    weekday: WEEKDAY_TO_INDEX[mapped.weekday],
  };
}

function zonedDateTimeToUtcMs({ year, month, day, hour, minute, second }, timeZone) {
  let utcMs = Date.UTC(year, month - 1, day, hour, minute, second);
  const formatter = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone,
  });

  for (let i = 0; i < 4; i += 1) {
    const parts = formatter.formatToParts(new Date(utcMs));
    const mapped = {};
    for (const part of parts) {
      if (part.type !== "literal") {
        mapped[part.type] = part.value;
      }
    }

    const observed = Date.UTC(
      Number(mapped.year),
      Number(mapped.month) - 1,
      Number(mapped.day),
      Number(mapped.hour),
      Number(mapped.minute),
      Number(mapped.second),
    );
    const target = Date.UTC(year, month - 1, day, hour, minute, second);
    const delta = target - observed;
    if (delta === 0) {
      break;
    }
    utcMs += delta;
  }

  return utcMs;
}

function getSecondsToWeekend(now) {
  const warsawNow = getWarsawParts(now);
  let daysUntilFriday = (5 - warsawNow.weekday + 7) % 7;
  const isAfterFridayStart =
    warsawNow.weekday === 5 && (warsawNow.hour > 17 || (warsawNow.hour === 17 && (warsawNow.minute > 0 || warsawNow.second > 0)));

  if (daysUntilFriday === 0 && isAfterFridayStart) {
    daysUntilFriday = 7;
  }

  const targetUtcMs = zonedDateTimeToUtcMs(
    {
      year: warsawNow.year,
      month: warsawNow.month,
      day: warsawNow.day + daysUntilFriday,
      hour: 17,
      minute: 0,
      second: 0,
    },
    WARSAW_TIME_ZONE,
  );

  return Math.max(0, Math.floor((targetUtcMs - now.getTime()) / 1000));
}

function formatCountdown(secondsLeft) {
  const days = Math.floor(secondsLeft / 86400);
  const hours = Math.floor((secondsLeft % 86400) / 3600);
  const minutes = Math.floor((secondsLeft % 3600) / 60);
  const seconds = secondsLeft % 60;
  return { days, hours, minutes, seconds };
}

function getPolishPluralLabel(value, one, few, many) {
  const abs = Math.abs(value);
  const mod10 = abs % 10;
  const mod100 = abs % 100;

  if (abs === 1) {
    return one;
  }
  if (mod10 >= 2 && mod10 <= 4 && !(mod100 >= 12 && mod100 <= 14)) {
    return few;
  }
  return many;
}

function getUkrainianPluralLabel(value, one, few, many) {
  const abs = Math.abs(value);
  const mod10 = abs % 10;
  const mod100 = abs % 100;

  if (mod10 === 1 && mod100 !== 11) {
    return one;
  }
  if (mod10 >= 2 && mod10 <= 4 && !(mod100 >= 12 && mod100 <= 14)) {
    return few;
  }
  return many;
}

export default {
  name: "AppHeader",
  setup() {
    const formattedDateTime = ref("");
    const weekendCountdownText = ref("");
    const isOpen = ref(false);
    const runtimeInfo = ref({
      version: "loading...",
      codename: "loading...",
      commit: "loading...",
    });
    const buildInfo = ref({
      version: "loading...",
      codename: "loading...",
      uiSrcVersion: "loading...",
      commit: "loading...",
      builtAt: "loading...",
    });
    const queueInfo = ref({
      serverActive: 0,
      queued: 0,
      running: 0,
      done: 0,
      error: 0,
      errorMessage: "",
      enabled: false,
    });

    const queueTooltip = computed(() => {
      if (!queueInfo.value.enabled) {
        return "PMS disabled";
      }
      if (queueInfo.value.errorMessage) {
        return `PMS error: ${queueInfo.value.errorMessage}`;
      }
      return `queued=${queueInfo.value.queued} running=${queueInfo.value.running} done=${queueInfo.value.done} error=${queueInfo.value.error}`;
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
      const zonePart = warsawTimeZoneFormatter
        .formatToParts(now)
        .find((part) => part.type === "timeZoneName")?.value;

      formattedDateTime.value = `${warsawDateFormatter.format(now)} ${zonePart || "CET"}`;

      const secondsToWeekend = getSecondsToWeekend(now);
      const countdown = formatCountdown(secondsToWeekend);

      let unitLabels;
      if (locale.value === "pl") {
        unitLabels = {
          days: getPolishPluralLabel(countdown.days, t("appInfo.daysOne"), t("appInfo.daysFew"), t("appInfo.daysMany")),
          hours: getPolishPluralLabel(countdown.hours, t("appInfo.hoursOne"), t("appInfo.hoursFew"), t("appInfo.hoursMany")),
          minutes: getPolishPluralLabel(
            countdown.minutes,
            t("appInfo.minutesOne"),
            t("appInfo.minutesFew"),
            t("appInfo.minutesMany"),
          ),
          seconds: getPolishPluralLabel(
            countdown.seconds,
            t("appInfo.secondsOne"),
            t("appInfo.secondsFew"),
            t("appInfo.secondsMany"),
          ),
        };
      } else if (locale.value === "uk") {
        unitLabels = {
          days: getUkrainianPluralLabel(countdown.days, t("appInfo.daysOne"), t("appInfo.daysFew"), t("appInfo.daysMany")),
          hours: getUkrainianPluralLabel(countdown.hours, t("appInfo.hoursOne"), t("appInfo.hoursFew"), t("appInfo.hoursMany")),
          minutes: getUkrainianPluralLabel(
            countdown.minutes,
            t("appInfo.minutesOne"),
            t("appInfo.minutesFew"),
            t("appInfo.minutesMany"),
          ),
          seconds: getUkrainianPluralLabel(
            countdown.seconds,
            t("appInfo.secondsOne"),
            t("appInfo.secondsFew"),
            t("appInfo.secondsMany"),
          ),
        };
      } else {
        unitLabels = {
          days: t("appInfo.days"),
          hours: t("appInfo.hours"),
          minutes: t("appInfo.minutes"),
          seconds: t("appInfo.seconds"),
        };
      }

      weekendCountdownText.value =
        `${t("appInfo.weekendCountdownPrefix")} ` +
        `${countdown.days} ${unitLabels.days}, ` +
        `${countdown.hours} ${unitLabels.hours}, ` +
        `${countdown.minutes} ${unitLabels.minutes}, ` +
        `${countdown.seconds} ${unitLabels.seconds}`;
    };

    let intervalId = null;
    let queueIntervalId = null;

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
          uiSrcVersion: "unknown",
          commit: "unknown",
          builtAt: "unknown",
        };
      }
    };

    const loadPerceptualQueue = async () => {
      try {
        const payload = await fetchPerceptualQueue();
        queueInfo.value = {
          serverActive: Number(payload?.server_active || 0),
          queued: Number(payload?.queued || 0),
          running: Number(payload?.running || 0),
          done: Number(payload?.done || 0),
          error: Number(payload?.error || 0),
          errorMessage: String(payload?.error_message || ""),
          enabled: Boolean(payload?.enabled),
        };
      } catch (error) {
        queueInfo.value.errorMessage = error?.message || "unknown";
      }
    };

    onMounted(() => {
      updateDateTime();
      intervalId = setInterval(updateDateTime, 1000);
      document.addEventListener("click", handleClickOutside);
      loadAppInfo();
      loadPerceptualQueue();
      queueIntervalId = setInterval(loadPerceptualQueue, 5000);
    });

    onUnmounted(() => {
      if (intervalId) {
        clearInterval(intervalId);
      }
      if (queueIntervalId) {
        clearInterval(queueIntervalId);
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
      weekendCountdownText,
      runtimeInfo,
      buildInfo,
      queueInfo,
      queueTooltip,
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
  min-width: 170px;
}

.datetime-tooltip {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: default;
  outline: none;
}

.datetime-tooltip-content {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: max-content;
  max-width: 320px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.16);
  color: var(--body-color);
  font-size: 12px;
  line-height: 1.35;
  z-index: 30;
  opacity: 0;
  visibility: hidden;
  transform: translateY(4px);
  transition: opacity 0.18s ease, transform 0.18s ease, visibility 0.18s ease;
  pointer-events: none;
}

.datetime-tooltip:hover .datetime-tooltip-content,
.datetime-tooltip:focus .datetime-tooltip-content,
.datetime-tooltip:focus-visible .datetime-tooltip-content {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.datetime-wrap {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.perceptual-queue {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--body-color);
  font-size: 11px;
}

.perceptual-queue--error {
  border-color: #b42318;
  color: #b42318;
}

.perceptual-queue-label {
  font-weight: 700;
}

.perceptual-queue-value {
  min-width: 1.2rem;
  text-align: right;
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
