<template>
  <div class="modal fade" id="vrtModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-fullscreen modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header justify-content-between align-items-start">
          <div class="modal-header-content">
            <div class="modal-header-main">
              <div class="mono fw-semibold">{{ viewer.modalTitle }}</div>
              <div class="text-muted small mono">{{ viewer.modalSubtitle }}</div>
            </div>
            <div class="modal-header-meta">
              <div v-if="headerBadges.length" class="modal-header-badges">
                <span v-for="badge in headerBadges" :key="badge.key" class="badge" :class="badge.class" :style="badge.style">
                  {{ badge.label }}
                </span>
              </div>
              <div v-if="scoringText" class="modal-scoring-text">{{ scoringText }}</div>
            </div>
          </div>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>

        <div class="modal-body d-flex flex-column"
             @mousemove="onMouseMove"
             @mouseleave="$emit('reset-cursor')">

          <div class="d-flex flex-wrap gap-2 align-items-center mb-3 toolbar">
            <div class="btn-group btn-group-sm" role="group">
              <button v-for="count in [1,2,3,4]" :key="count"
                      type="button"
                      class="btn"
                      :class="viewer.columns===count ? 'btn-primary' : 'btn-outline-secondary'"
                      @click="$emit('set-columns', count)">
                {{ count }}
              </button>
            </div>

            <div class="btn-group btn-group-sm" role="group">
              <button type="button" class="btn" :class="keyHeld.a ? 'btn-primary' : 'btn-outline-secondary'" @mousedown="keyHeld.a=true" @mouseup="keyHeld.a=false" @click="$emit('navigate', -1)">← K-A</button>
              <button type="button" class="btn" :class="keyHeld.d ? 'btn-primary' : 'btn-outline-secondary'" @mousedown="keyHeld.d=true" @mouseup="keyHeld.d=false" @click="$emit('navigate', 1)">K-D →</button>
            </div>

            <button type="button" :class="superZoomActive ? 'btn btn-primary ms-1' : 'btn btn-outline-secondary ms-1'"
                    @pointerdown.prevent="$emit('super-zoom-down')"
                    @pointerup.prevent="$emit('super-zoom-up')"
                    @pointerleave.prevent="$emit('super-zoom-up')">
              🔍 K-W
            </button>

            <div class="btn-group btn-group-sm" role="group">
              <button v-if="!viewer.tags.bug" type="button" class="btn btn-outline-danger" @click="$emit('prompt-tag','bug')">{{ t('tags.bug') }}! (K-S)</button>
              <button v-if="viewer.tags.bug" type="button" class="btn btn-danger btn-sm" @click="$emit('prompt-remove-tag','bug')">{{ t('tags.bug') }} ✕</button>
              <button v-if="!viewer.tags.aso" type="button" class="btn btn-outline-warning text-dark" @click="$emit('prompt-tag','aso')">{{ t('tags.aso') }} (K-C)</button>
              <button v-if="viewer.tags.aso" type="button" class="btn btn-warning btn-sm text-dark" @click="$emit('prompt-remove-tag','aso')">{{ t('tags.aso') }} ✕</button>
              <button v-if="!viewer.tags.baseline" type="button" class="btn btn-outline-success text-success" @click="$emit('prompt-tag','baseline')">{{ t('tags.baseline') }} (K-\)</button>
              <button v-if="viewer.tags.baseline" type="button" class="btn btn-success btn-sm" @click="$emit('prompt-remove-tag','baseline')">{{ t('tags.baseline') }} ✕</button>
            </div>

            <button type="button" class="btn btn-outline-secondary btn-sm ms-auto" @click="$emit('close-modal')">{{ t('modal.exit') }}</button>
          </div>

          <div class="text-muted small mb-2">{{ t('modal.keys') }}</div>

          <div class="flex-grow-1 overflow-auto pb-2 position-relative">
            <div class="slot-grid" :style="gridStyle">
              <div v-for="slot in viewer.slots" :key="slot.id" class="slot-card">
                <div class="slot-header d-flex justify-content-between align-items-center">
                  <div class="mono small">{{ t('modal.slot') }} {{ slot.id }}</div>
                  <div class="d-flex align-items-center gap-2">
                    <select class="form-select form-select-sm slot-mode-select"
                            :value="slot.mode"
                            @change="$emit('set-slot-mode', slot.id, $event.target.value)">
                      <option v-for="mode in modeOptions" :key="mode.value" :value="mode.value">
                        {{ mode.label }}
                      </option>
                    </select>
              </div>
                </div>
                <div class="slot-divider"></div>
                <div class="slot-media">
                  <img v-if="slotImage(slot)" :src="slotImage(slot)"
                       :style="[presentationStyle, imageStyle]" />
                  <div v-else class="text-muted small text-center position-absolute top-50 start-50 translate-middle">
                    {{ t('modal.noImage') }} {{ slotModeLabel(slot.mode) }}
                  </div>
                </div>
              </div>
            </div>

            <div v-if="prompt.active" class="prompt-overlay">
              <div class="prompt-card">
                <div class="prompt-title">{{ t('prompt.confirm') }}</div>
                <div class="prompt-text">{{ promptRemove ? t('prompt.removeTag') : t('prompt.areYouSure') }} {{ promptTypeLabel(prompt.type) }}?</div>
                <div class="prompt-hints">{{ t('prompt.shiftNo') }} &nbsp;•&nbsp; {{ t('prompt.spaceYes') }}</div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { fmt } from "../lib/format";
import { badgeStyle } from "../lib/badgeStyle";
import { t } from "../lib/i18n";

export default {
  name: "ViewerModal",
  props: {
    viewer: { type: Object, required: true },
    gridStyle: { type: Object, default: () => ({}) },
    presentationStyle: { type: Object, default: () => ({}) },
    imageStyle: { type: Object, default: () => ({}) },
    prompt: { type: Object, default: () => ({ active: false, type: null }) },
    keyHeld: { type: Object, default: () => ({}) },
    superZoomActive: { type: Boolean, default: false },
    slotImage: { type: Function, required: true },
  },
  emits: [
    "set-columns",
    "set-slot-mode",
    "navigate",
    "super-zoom-down",
    "super-zoom-up",
    "prompt-tag",
    "prompt-remove-tag",
    "close-modal",
    "reset-cursor",
    "mouse-move",
  ],
  computed: {
    promptRemove() {
      return this.prompt.type?.startsWith("remove-");
    },
    modeOptions() {
      return [
        { value: "ref", label: "REF" },
        { value: "test", label: "TEST" },
        { value: "diff", label: "PIXEL_DIFF" },
        { value: "lpips", label: "PERC" },
      ];
    },
    headerBadges() {
      const row = this.viewer.modalRow || {};
      const badges = [];
      if (row.status) {
        badges.push({
          key: `status-${row.status}`,
          label: this.statusLabel(row.status),
          class: this.statusClass(row.status),
        });
      }
      if (row.viewport) {
        badges.push({
          key: `viewport-${row.viewport}`,
          label: row.viewport,
          style: badgeStyle("viewport", row.viewport),
        });
      }
      if (row.browser) {
        badges.push({
          key: `browser-${row.browser}`,
          label: row.browser,
          style: badgeStyle("browser", row.browser),
        });
      }
      const tags = this.viewer.tags || {};
      const mapping = [
        { key: "bug", label: this.t("tags.bug"), class: "bg-danger" },
        { key: "aso", label: this.t("tags.aso"), class: "bg-warning text-dark" },
        { key: "baseline", label: this.t("tags.baseline"), class: "bg-success" },
      ];
      const tagBadges = mapping.filter((badge) => tags[badge.key]);
      return [...badges, ...tagBadges];
    },
    scoringText() {
      const row = this.viewer.modalRow || {};
      const hasData = ["pixel_changed_ratio", "lpips", "dists"].some(
        (key) => row[key] !== undefined && row[key] !== null && row[key] !== ""
      );
      if (!hasData) return "";
      const pixel = this.fmt(row.pixel_changed_ratio) || "—";
      const lpips = this.fmt(row.lpips) || "—";
      const dists = this.fmt(row.dists) || "—";
      return `${this.t("modal.scoringLabel")}: ${this.t("modal.scoringPixel")} ${pixel} / ${this.t(
        "modal.scoringLpips"
      )} ${lpips} / ${this.t("modal.scoringDists")} ${dists}`;
    },
  },
  methods: {
    t(key) {
      return t(key);
    },
    fmt,
    onMouseMove(evt) {
      const bounds = evt.currentTarget?.getBoundingClientRect();
      this.$emit('mouse-move', { bounds, evt });
    },
    slotModeLabel(mode) {
      const match = this.modeOptions.find((item) => item.value === mode);
      return match ? match.label : "";
    },
    statusClass(status) {
      if (status === 'passed') return 'text-bg-success';
      if (status === 'failed') return 'text-bg-danger';
      if (status === 'skipped' || status === 'new') return 'text-bg-warning';
      if (status === 'error') return 'text-bg-dark';
      return '';
    },
    statusLabel(status) {
      if (!status) return '';
      const normalized = String(status).toLowerCase();
      const key = `status.${normalized}`;
      const translation = this.t(key);
      if (translation && translation !== key) {
        return translation;
      }
      return status;
    },
    promptTypeLabel(type) {
      const tagType = type?.replace("remove-", "") || type;
      if (tagType === "bug") return t('tags.bug');
      if (tagType === "aso") return t('tags.aso');
      if (tagType === "baseline") return t('tags.baseline');
      return "";
    },
  },
};
</script>

<style scoped>
.modal-header-content {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 0.35rem;
}
.modal-header-main {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}
.modal-header-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.modal-header-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.modal-scoring-text {
  font-size: 0.85rem;
  color: var(--text-muted);
  letter-spacing: 0.02em;
}

.slot-mode-select {
  background: var(--dropdown-gradient);
  color: var(--body-color);
  border-color: var(--border);
}

.slot-mode-select:focus,
.slot-mode-select:hover {
  background: var(--dropdown-gradient);
  color: var(--body-color);
  border-color: var(--primary);
}

.slot-mode-select option {
  background-color: var(--card-bg);
  color: var(--body-color);
}
</style>
