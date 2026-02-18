<template>
  <div>
    <div class="d-flex align-items-center justify-content-between mb-3">
      <div>
        <h3 class="mb-0">{{ t('report.title') }}</h3>
        <div class="text-muted small">{{ t('report.run') }}: <span class="mono">{{ runId || "unknown" }}</span></div>
      </div>
      <div class="d-flex align-items-center gap-2">
        <div class="btn-group btn-group-sm" role="group" aria-label="tag persistence">
          <button type="button" class="btn btn-outline-secondary" @click="triggerTagImport">{{ t('report.importTags') }}</button>
          <button type="button" class="btn btn-outline-secondary" @click="exportTags">{{ t('report.exportTags') }}</button>
          <button type="button" class="btn btn-outline-secondary" @click="syncTagsToFile">{{ t('report.syncTags') }}</button>
          <button type="button" class="btn btn-success" @click="sendBaseline" :disabled="baselineCandidates.length === 0">
            {{ t('report.sendBaseline') }} ({{ baselineCandidates.length }})
          </button>
        </div>
        <input
          ref="tagFileInput"
          type="file"
          accept="application/json"
          class="d-none"
          @change="onTagFileSelected"
        />
        <div v-if="tagSyncMessage" class="text-muted small">{{ tagSyncMessage }}</div>
        <div v-if="baselineMessage" class="text-muted small">{{ baselineMessage }}</div>
        <div class="text-muted small mono">{{ store.summary }}</div>
      </div>
    </div>

    <div v-if="loadError" class="alert alert-danger py-2">{{ loadError }}</div>

    <FiltersPanel :store="store" @reset="reset" />
    <ResultsTable 
      :rows="rows" 
      :fmt="fmt" 
      :tag-log="viewer.tagLog" 
      :tag-key-for-row="getRowTagKey"
      :selected-index="selectedIndex"
      @show="show"
      @select="selectRow"
    />
    <div v-if="selectedIndex >= 0" class="keyboard-hint text-muted small mb-2">
      {{ t('navigate.backToHero') }}
    </div>
    <ViewerModal
      :viewer="viewer"
      :grid-style="gridStyle"
      :presentation-style="presentationStyle"
      :image-style="imageStyle"
      :prompt="prompt"
      :key-held="keyHeld"
      :super-zoom-active="superZoomActive"
      :slot-image="slotImage"
      @set-columns="setColumns"
      @set-slot-mode="setSlotMode"
      @navigate="navigate"
      @super-zoom-down="handleSuperZoomPointerDown"
      @super-zoom-up="handleSuperZoomPointerUp"
      @prompt-tag="promptTag"
      @close-modal="closeModal"
      @reset-cursor="resetCursor"
      @mouse-move="handleMouseMove"
    />
  </div>
</template>

<script>
import FiltersPanel from "../components/FiltersPanel.vue";
import ResultsTable from "../components/ResultsTable.vue";
import ViewerModal from "../components/ViewerModal.vue";
import { fmt } from "../lib/format";
import { t } from "../lib/i18n";
import { createStore, filteredSorted, resetFilters, setRows } from "../lib/store";
import {
  loadTagSnapshot,
  persistTagSnapshot,
  downloadTagSnapshot,
  parseTagFile,
  saveTagSnapshotToFile,
} from "../lib/tagPersistence";
import { requestBaselineChallengeForRun, sendBaselineSelectionForRun } from "../lib/baselineApi";
import { fetchReportResults } from "../lib/api/reportsApi";
import {
  createViewerState,
  ensureModal,
  openViewer,
  getModeSrc,
  refreshSlots,
  navigateRow,
  setCursorPosition,
  toggleTag,
  getRowTagKey as buildRowTagKey,
} from "../lib/viewer";

export default {
  name: "ReportPage",
  components: {
    FiltersPanel,
    ResultsTable,
    ViewerModal,
  },
  props: {
    runId: {
      type: String,
      default: "",
    },
  },
  data() {
    return {
      store: createStore(),
      viewer: createViewerState(),
      baseZoom: 100,
      superZoomActive: false,
      keyHeld: { a: false, d: false, w: false, s: false, c: false },
      prompt: { active: false, type: null },
      tagSyncTimer: null,
      tagSyncMessage: "",
      baselineMessage: "",
      loadError: "",
      selectedIndex: -1,
    };
  },
  computed: {
    rows() {
      return filteredSorted(this.store);
    },
    gridStyle() {
      const requested = Math.max(1, this.viewer.columns || 1);
      const columns = requested === 4 ? 2 : requested;
      return {
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
        alignContent: requested === 4 ? "center" : "start",
        gridAutoRows: "1fr",
      };
    },
    zoomScale() {
      const level = this.superZoomActive ? this.baseZoom + 200 : this.baseZoom;
      return level / 100;
    },
    presentationStyle() {
      return {
        width: "100%",
        height: "100%",
        objectFit: "contain",
        objectPosition: "center",
      };
    },
    imageStyle() {
      const scale = this.zoomScale;
      return {
        transform: `scale(${scale})`,
        transformOrigin: `${this.viewer.cursorX}% ${this.viewer.cursorY}%`,
      };
    },
    baselineCandidates() {
      return this.store.rows.filter((row) => {
        const key = this.getRowTagKey(row);
        const tags = this.viewer.tagLog?.[key];
        return !!(tags?.baseline && row?.actual_path);
      });
    },
  },
  methods: {
    t(key) {
      return t(key);
    },
    fmt,
    async loadResults() {
      this.loadError = "";
      if (!this.runId) {
        setRows(this.store, []);
        this.loadError = "Missing run id in URL";
        return;
      }
      try {
        const rows = await fetchReportResults(this.runId);
        setRows(this.store, rows);
      } catch (error) {
        setRows(this.store, []);
        this.loadError = `Unable to load results: ${error?.message || "unknown error"}`;
      }
    },
    getRowTagKey(row) {
      return buildRowTagKey(row);
    },
    normalizeTagLog(snapshot) {
      if (!snapshot || typeof snapshot !== "object") return {};
      const normalized = {};
      for (const [key, tags] of Object.entries(snapshot)) {
        if (!tags || typeof tags !== "object") continue;
        normalized[key] = {
          bug: !!tags.bug,
          aso: !!tags.aso,
          baseline: !!tags.baseline,
        };
      }
      return normalized;
    },
    async loadTags() {
      const snapshot = await loadTagSnapshot();
      if (!snapshot || typeof snapshot !== "object") return;
      this.viewer.tagLog = this.normalizeTagLog(snapshot);
      persistTagSnapshot(this.viewer.tagLog);
    },
    persistTags() {
      persistTagSnapshot(this.viewer.tagLog);
      this.scheduleTagFileSync();
    },
    scheduleTagFileSync() {
      if (this.tagSyncTimer) {
        window.clearTimeout(this.tagSyncTimer);
      }
      this.tagSyncTimer = window.setTimeout(async () => {
        const synced = await saveTagSnapshotToFile(this.viewer.tagLog);
        this.tagSyncMessage = synced ? "tags synced to file" : "tags saved locally";
      }, 250);
    },
    triggerTagImport() {
      this.$refs.tagFileInput?.click();
    },
    async onTagFileSelected(evt) {
      const input = evt?.target;
      const file = input?.files?.[0];
      const parsed = await parseTagFile(file);
      input.value = "";
      if (!parsed || typeof parsed !== "object") return;
      this.viewer.tagLog = this.normalizeTagLog({ ...this.viewer.tagLog, ...parsed });
      this.persistTags();
    },
    exportTags() {
      downloadTagSnapshot(this.viewer.tagLog);
    },
    async syncTagsToFile() {
      const synced = await saveTagSnapshotToFile(this.viewer.tagLog);
      this.tagSyncMessage = synced ? "tags synced to file" : "file sync unavailable; local only";
      persistTagSnapshot(this.viewer.tagLog);
    },
    async sendBaseline() {
      const candidates = this.baselineCandidates;
      if (!candidates.length) {
        this.baselineMessage = "No BASELINE-tagged TEST artifacts selected";
        return;
      }

      let challenge;
      try {
        challenge = await requestBaselineChallengeForRun(this.runId);
      } catch (_error) {
        this.baselineMessage = "SEND BASELINE requires report server (run make visual-report-serve)";
        return;
      }

      const phrase = String(challenge?.phrase || "").trim();
      const challengeId = String(challenge?.challenge_id || "").trim();
      if (!phrase || !challengeId) {
        this.baselineMessage = "Unable to start baseline confirmation challenge";
        return;
      }

      const typed = window.prompt(`Type this phrase to confirm baseline write:\n\n${phrase}`);
      if (typed === null) {
        this.baselineMessage = "SEND BASELINE cancelled";
        return;
      }

      const items = candidates.map((row) => ({
        scenario_id: row.scenario_id || "",
        suite_id: row.suite_id || "",
        viewport: row.viewport || "",
        browser: row.browser || "",
        actual_path: row.actual_path || "",
      }));

      try {
        const response = await sendBaselineSelectionForRun(this.runId, {
          challenge_id: challengeId,
          phrase: String(typed).trim(),
          items,
        });
        const saved = Number(response?.saved_count || 0);
        const failed = Number(response?.failed_count || 0);
        this.baselineMessage = `Baseline sync done: saved=${saved}, failed=${failed}`;
      } catch (error) {
        this.baselineMessage = `SEND BASELINE failed: ${error?.message || "unknown error"}`;
      }
    },
    reset() {
      resetFilters(this.store);
    },
    show(row, mode, index = null) {
      const fallbackMode = this.viewer.viewerMode || "test";
      const normalizedMode = mode === "compare" ? fallbackMode : (mode || fallbackMode);
      openViewer(this.viewer, row, normalizedMode, index, { runId: this.runId });
      ensureModal(this.viewer, "vrtModal").show();
    },
    slotImage(slot) {
      return getModeSrc(this.viewer, slot?.mode) || "";
    },
    setSlotMode(slotId, mode) {
      const slot = this.viewer.slots.find((item) => item.id === slotId);
      if (!slot) return;
      slot.mode = mode;
      if (!this.viewer.slotModes) {
        this.viewer.slotModes = {};
      }
      this.viewer.slotModes[slotId] = mode;
    },
    setColumns(value) {
      this.viewer.columns = value;
      refreshSlots(this.viewer, value);
    },
    selectRow(index) {
      this.selectedIndex = index;
    },
    navigateSelection(delta) {
      const newIndex = this.selectedIndex + delta;
      if (newIndex >= 0 && newIndex < this.rows.length) {
        this.selectedIndex = newIndex;
      } else if (newIndex < 0 && this.rows.length > 0) {
        this.selectedIndex = 0;
      } else if (newIndex >= this.rows.length && this.rows.length > 0) {
        this.selectedIndex = this.rows.length - 1;
      }
    },
    openSelectedRow() {
      if (this.selectedIndex >= 0 && this.selectedIndex < this.rows.length) {
        const row = this.rows[this.selectedIndex];
        this.show(row, "test", this.selectedIndex);
      }
    },
    goToHero() {
      window.history.pushState({}, "", "/");
      window.dispatchEvent(new PopStateEvent("popstate"));
    },
    handleKeydown(evt) {
      const modalEl = document.getElementById("vrtModal");
      const isOpen = modalEl && modalEl.classList.contains("show");

      if (!isOpen) {
        this.handleKeydownNonModal(evt);
        return;
      }

      if (this.prompt.active) {
        if (evt.code === "Space") {
          this.confirmPrompt();
        } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
          this.cancelPrompt();
        }
        return;
      }

      const k = evt.key;

      if (["1", "2", "3", "4"].includes(k)) {
        this.setColumns(Number(k));
      } else if (k.toUpperCase() === "A") {
        evt.preventDefault();
        this.keyHeld.a = true;
        this.navigate(-1);
      } else if (k.toUpperCase() === "D") {
        evt.preventDefault();
        this.keyHeld.d = true;
        this.navigate(1);
      } else if (k.toUpperCase() === "W") {
        if (!this.superZoomActive) {
          this.keyHeld.w = true;
          this.activateSuperZoom();
        }
      } else if (k.toUpperCase() === "S") {
        if (!this.isTagLocked("bug")) {
          this.promptTag("bug");
        }
      } else if (k.toUpperCase() === "C") {
        if (!this.isTagLocked("aso")) {
          this.promptTag("aso");
        }
      } else if (k === "\\") {
        if (!this.isTagLocked("baseline")) {
          this.promptTag("baseline");
        }
      } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
        this.closeModal();
      } else if (k === "Escape") {
        this.viewer.modal?.hide();
      }
    },
    handleKeydownNonModal(evt) {
      if (this.prompt.active) {
        if (evt.code === "Space") {
          this.confirmPrompt();
        } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
          this.cancelPrompt();
        }
        return;
      }

      const k = evt.key;

      if (evt.code === "ArrowUp") {
        evt.preventDefault();
        this.navigateSelection(-1);
      } else if (evt.code === "ArrowDown") {
        evt.preventDefault();
        this.navigateSelection(1);
      } else if (evt.code === "Space") {
        evt.preventDefault();
        this.openSelectedRow();
      } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
        this.goToHero();
      } else if (k === "Escape") {
        this.selectedIndex = -1;
      }
    },
    handleKeyup(evt) {
      const k = evt.key;
      if (k.toUpperCase() === "A") this.keyHeld.a = false;
      if (k.toUpperCase() === "D") this.keyHeld.d = false;
      if (k.toUpperCase() === "W") {
        this.keyHeld.w = false;
        this.deactivateSuperZoom();
      }
    },
    handleSuperZoomPointerDown() {
      if (!this.superZoomActive) {
        this.keyHeld.w = true;
        this.activateSuperZoom();
      }
    },
    handleSuperZoomPointerUp() {
      if (this.superZoomActive) {
        this.keyHeld.w = false;
        this.deactivateSuperZoom();
      }
    },
    activateSuperZoom() {
      this.superZoomActive = true;
    },
    deactivateSuperZoom() {
      this.superZoomActive = false;
    },
    navigate(offset) {
      const next = navigateRow(this.viewer, this.rows, offset);
      if (next) {
        this.show(next.row, this.viewer.viewerMode, next.index);
      }
    },
    isTagLocked(type) {
      const row = this.viewer.modalRow;
      if (!row) return false;
      const key = this.getRowTagKey(row);
      return !!this.viewer.tagLocked?.[key]?.[type];
    },
    promptTag(type) {
      if (this.prompt.active) return;
      if (this.isTagLocked(type)) return;
      this.prompt = { active: true, type };
    },
    confirmPrompt() {
      if (!this.prompt.active) return;
      toggleTag(this.viewer, this.viewer.modalRow, this.prompt.type);
      this.persistTags();
      this.prompt = { active: false, type: null };
    },
    cancelPrompt() {
      if (!this.prompt.active) return;
      this.prompt = { active: false, type: null };
    },
    closeModal() {
      this.viewer.modal?.hide();
      this.deactivateSuperZoom();
      this.cancelPrompt();
    },
    handleMouseMove(payload) {
      const bounds = payload?.bounds;
      const evt = payload?.evt;
      if (!bounds || !evt) return;
      setCursorPosition(this.viewer, bounds, evt);
    },
    resetCursor() {
      this.viewer.cursorX = 50;
      this.viewer.cursorY = 50;
    },
  },
  async mounted() {
    await this.loadResults();
    await this.loadTags();
    window.addEventListener("keydown", this.handleKeydown);
    window.addEventListener("keyup", this.handleKeyup);
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleKeydown);
    window.removeEventListener("keyup", this.handleKeyup);
    if (this.tagSyncTimer) {
      window.clearTimeout(this.tagSyncTimer);
      this.tagSyncTimer = null;
    }
  },
};
</script>

<style>
.thumb { max-width: 220px; max-height: 120px; object-fit: contain; cursor: zoom-in; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.small-col { white-space: nowrap; }
.modal-full {
  max-width: calc(100vw - 24px);
  width: calc(100vw - 24px);
  height: calc(100vh - 24px);
  margin: 0 auto;
}
.modal-full .modal-dialog {
  height: 100%;
}
.modal-full .modal-content {
  height: 100%;
  border-radius: 1rem;
  overflow: hidden;
}
.modal-full .modal-body {
  height: calc(100vh - 24px - 72px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.slot-mode-select {
  min-width: 110px;
}
.slot-grid {
  display: grid;
  gap: 1rem;
  height: 100%;
}
.slot-card {
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  background: var(--card-bg);
  padding: 0.5rem 0.75rem 0.25rem;
  display: flex;
  flex-direction: column;
  min-height: 220px;
  position: relative;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.slot-divider {
  height: 1px;
  background: var(--border);
  margin: 0.25rem 0;
}
.slot-media {
  flex: 1;
  position: relative;
  overflow: hidden;
  min-height: 210px;
}
.slot-media img {
  transition: transform-origin var(--zoom-origin-ease-ms, 80ms) ease;
}
.prompt-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}
.prompt-card {
  background: var(--card-bg);
  padding: 1.25rem 1.5rem;
  border-radius: 0.75rem;
  box-shadow: 0 20px 45px rgba(0,0,0,0.2);
  text-align: center;
  max-width: 360px;
  width: 100%;
}
.prompt-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
}
.prompt-text {
  margin-bottom: 0.5rem;
}
.prompt-hints {
  color: var(--text-muted);
  font-size: 0.85rem;
}
.keyboard-hint {
  padding: 0.5rem;
  background: var(--card-bg);
  border-radius: 0.25rem;
}
</style>
