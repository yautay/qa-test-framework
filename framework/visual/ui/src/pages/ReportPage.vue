<template>
  <div class="report-wrap">
    <AppHeader />
    <section class="report-header mb-3 p-4 rounded-4">
      <div class="d-flex align-items-center justify-content-between">
        <div>
          <h3 class="mb-0">{{ t('report.title') }}</h3>
          <div class="text-muted small">{{ t('report.run') }}: <span class="mono">{{ runId || "unknown" }}</span></div>
        </div>
        <div class="d-flex align-items-center gap-2">
          <div class="btn-group btn-group-sm" role="group" aria-label="tag persistence">
            <button type="button" class="btn btn-success" @click="sendBaseline" :disabled="baselineCandidates.length === 0">
              {{ t('report.sendBaseline') }} ({{ baselineCandidates.length }})
            </button>
          </div>
          <div v-if="tagSyncMessage" class="text-muted small">{{ tagSyncMessage }}</div>
          <div v-if="baselineMessage" class="text-muted small">{{ baselineMessage }}</div>
          <div class="text-muted small mono">{{ store.summary }}</div>
        </div>
      </div>
    </section>

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
      @open-note="openNoteFromTable"
      @open-metadata="openMetadataFromTable"
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
      :note-editor="noteEditor"
      :note-max-length="noteMaxLength"
      :key-held="keyHeld"
      :super-zoom-active="superZoomActive"
      :slot-image="slotImage"
      @set-columns="setColumns"
      @set-slot-mode="setSlotMode"
      @navigate="navigate"
      @super-zoom-down="handleSuperZoomPointerDown"
      @super-zoom-up="handleSuperZoomPointerUp"
      @prompt-tag="promptTag"
      @prompt-remove-tag="promptRemoveTag"
      @open-note="openNoteEditor"
      @open-metadata="openMetadataFromModal"
      @note-input="updateNoteDraft"
      @save-note="saveNoteFromEditor"
      @cancel-note="cancelNoteEditor"
      @delete-note="deleteNoteFromEditor"
      @close-modal="closeModal"
      @reset-cursor="resetCursor"
      @mouse-move="handleMouseMove"
    />
    <TestMetadataPanel
      :active="metadataPanel.active"
      :metadata="metadataPanel.payload"
      @close="closeMetadataPanel"
    />
  </div>
</template>

<script>
import AppHeader from "../components/AppHeader.vue";
import FiltersPanel from "../components/FiltersPanel.vue";
import ResultsTable from "../components/ResultsTable.vue";
import TestMetadataPanel from "../components/TestMetadataPanel.vue";
import ViewerModal from "../components/ViewerModal.vue";
import { fmt } from "../lib/format";
import { t } from "../lib/i18n";
import { createStore, filteredSorted, resetFilters, setRows } from "../lib/store";
import {
  loadTagSnapshot,
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
import {
  NOTE_MAX_LENGTH,
  normalizeNoteDraft as normalizeNoteDraftValue,
  normalizeTagLogSnapshot,
  sanitizeNoteText as sanitizeNoteTextValue,
} from "../lib/notes";

export default {
  name: "ReportPage",
  components: {
    AppHeader,
    FiltersPanel,
    ResultsTable,
    TestMetadataPanel,
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
      noteEditor: {
        active: false,
        rowKey: "",
        text: "",
        hasExisting: false,
      },
      metadataPanel: {
        active: false,
        payload: {},
      },
      noteMaxLength: NOTE_MAX_LENGTH,
    };
  },
  computed: {
    rows() {
      return filteredSorted(this.store, this.viewer.tagLog);
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
        this.selectedIndex = -1;
        this.loadError = "Missing run id in URL";
        return;
      }
      try {
        const rows = await fetchReportResults(this.runId);
        setRows(this.store, rows);
        if (this.rows.length > 0) {
          this.selectedIndex = 0;
        } else {
          this.selectedIndex = -1;
        }
      } catch (error) {
        setRows(this.store, []);
        this.selectedIndex = -1;
        this.loadError = `Unable to load results: ${error?.message || "unknown error"}`;
      }
    },
    getRowTagKey(row) {
      return buildRowTagKey(row);
    },
    normalizeTagLog(snapshot) {
      return normalizeTagLogSnapshot(snapshot);
    },
    sanitizeNoteText(raw) {
      return sanitizeNoteTextValue(raw);
    },
    normalizeNoteDraft(raw) {
      return normalizeNoteDraftValue(raw);
    },
    noteForRow(row) {
      const key = this.getRowTagKey(row);
      return this.viewer.tagLog?.[key]?.note || null;
    },
    ensureTagEntry(row) {
      const key = this.getRowTagKey(row);
      const existing = this.viewer.tagLog?.[key];
      if (existing) {
        if (!Object.prototype.hasOwnProperty.call(existing, "note")) {
          existing.note = null;
        }
        return { key, entry: existing };
      }
      this.viewer.tagLog[key] = {
        bug: false,
        aso: false,
        baseline: false,
        note: null,
      };
      return { key, entry: this.viewer.tagLog[key] };
    },
    async loadTags() {
      if (!this.runId) return;
      const snapshot = await loadTagSnapshot(this.runId);
      if (!snapshot || typeof snapshot !== "object") return;
      this.viewer.tagLog = this.normalizeTagLog(snapshot);
    },
    persistTags() {
      this.scheduleTagFileSync();
    },
    scheduleTagFileSync() {
      if (!this.runId) {
        this.tagSyncMessage = "missing run id, unable to save tags";
        return;
      }
      if (this.tagSyncTimer) {
        window.clearTimeout(this.tagSyncTimer);
      }
      const runId = this.runId;
      this.tagSyncTimer = window.setTimeout(async () => {
        const synced = await saveTagSnapshotToFile(this.viewer.tagLog, runId);
        this.tagSyncMessage = synced ? "tags saved on server" : "unable to save tags on server";
      }, 250);
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
    openNoteEditor(row = this.viewer.modalRow) {
      if (!row) return;
      if (this.prompt.active) return;
      const key = this.getRowTagKey(row);
      const note = this.noteForRow(row);
      this.noteEditor = {
        active: true,
        rowKey: key,
        text: note?.text || "",
        hasExisting: !!(note && note.text),
      };
    },
    openNoteFromTable(row, index) {
      if (typeof index === "number") {
        this.selectedIndex = index;
      }
      this.show(row, "test", index);
      this.openNoteEditor(row);
    },
    buildMetadataPayload(row) {
      const source = row && typeof row === "object" ? row : {};
      const candidate = source.test_metadata;
      const metadata = candidate && typeof candidate === "object" ? { ...candidate } : {};
      const runSection = metadata.run && typeof metadata.run === "object" ? { ...metadata.run } : {};
      runSection.run_id = runSection.run_id || this.runId || "";
      runSection.tester = runSection.tester || source.tester || "";
      runSection.run_note = runSection.run_note || source.run_note || "";
      metadata.run = runSection;

      const resultSection = metadata.result && typeof metadata.result === "object" ? { ...metadata.result } : {};
      resultSection.scenario_id = resultSection.scenario_id || source.scenario_id || "";
      resultSection.status = resultSection.status || source.status || "";
      resultSection.message = resultSection.message || source.message || "";
      resultSection.viewport = resultSection.viewport || source.viewport || "";
      resultSection.browser = resultSection.browser || source.browser || "";
      metadata.result = resultSection;
      return metadata;
    },
    openMetadataFromTable(row, index) {
      if (typeof index === "number") {
        this.selectedIndex = index;
      }
      this.metadataPanel = {
        active: true,
        payload: this.buildMetadataPayload(row),
      };
    },
    openMetadataFromModal() {
      this.metadataPanel = {
        active: true,
        payload: this.buildMetadataPayload(this.viewer.modalRow || {}),
      };
    },
    closeMetadataPanel() {
      this.metadataPanel = {
        active: false,
        payload: {},
      };
    },
    updateNoteDraft(value) {
      if (!this.noteEditor.active) return;
      const safeText = this.normalizeNoteDraft(value);
      this.noteEditor = {
        ...this.noteEditor,
        text: safeText,
      };
    },
    saveNoteFromEditor() {
      if (!this.noteEditor.active || !this.viewer.modalRow) return;
      const safeText = this.sanitizeNoteText(this.noteEditor.text);
      const { entry } = this.ensureTagEntry(this.viewer.modalRow);
      entry.note = safeText
        ? { text: safeText, updatedAt: new Date().toISOString() }
        : null;
      this.viewer.tags = { ...this.viewer.tags, note: entry.note };
      this.persistTags();
      this.cancelNoteEditor();
    },
    deleteNoteFromEditor() {
      if (!this.noteEditor.active || !this.viewer.modalRow) return;
      const { entry } = this.ensureTagEntry(this.viewer.modalRow);
      entry.note = null;
      this.viewer.tags = { ...this.viewer.tags, note: null };
      this.persistTags();
      this.cancelNoteEditor();
    },
    cancelNoteEditor() {
      if (!this.noteEditor.active) return;
      this.noteEditor = {
        active: false,
        rowKey: "",
        text: "",
        hasExisting: false,
      };
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

      if (this.noteEditor.active) {
        return;
      }

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
      } else if (k.toUpperCase() === "N") {
        this.openNoteEditor();
      } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
        this.closeModal();
      } else if (k === "Escape") {
        this.viewer.modal?.hide();
      }
    },
    handleKeydownNonModal(evt) {
      if (this.noteEditor.active) {
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
      if (this.noteEditor.active) {
        return;
      }
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
      if (this.noteEditor.active) return;
      if (this.isTagLocked(type)) return;
      this.prompt = { active: true, type };
    },
    promptRemoveTag(type) {
      if (this.prompt.active) return;
      if (this.noteEditor.active) return;
      this.prompt = { active: true, type: `remove-${type}` };
    },
    confirmPrompt() {
      if (!this.prompt.active) return;
      const type = this.prompt.type?.replace("remove-", "");
      if (this.prompt.type.startsWith("remove-")) {
        this.removeTag(type);
      } else {
        toggleTag(this.viewer, this.viewer.modalRow, type);
        this.persistTags();
      }
      this.prompt = { active: false, type: null };
    },
    removeTag(type) {
      const row = this.viewer.modalRow;
      if (!row) return;
      const key = this.getRowTagKey(row);
      if (this.viewer.tagLog[key]) {
        this.viewer.tagLog[key][type] = false;
      }
      if (this.viewer.tags) {
        this.viewer.tags[type] = false;
      }
      this.viewer.tagLocked = this.viewer.tagLocked || {};
      this.viewer.tagLocked[key] = this.viewer.tagLocked[key] || { bug: false, aso: false, baseline: false };
      this.viewer.tagLocked[key][type] = false;
      this.persistTags();
    },
    cancelPrompt() {
      if (!this.prompt.active) return;
      this.prompt = { active: false, type: null };
    },
    closeModal() {
      this.viewer.modal?.hide();
      this.deactivateSuperZoom();
      this.cancelPrompt();
      this.cancelNoteEditor();
      this.closeMetadataPanel();
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
.report-wrap {
  max-width: 1200px;
  margin: 0 auto;
}
.report-header {
  background: var(--hero-gradient);
  border: 1px solid var(--border);
}
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.keyboard-hint {
  padding: 0.5rem;
  background: var(--card-bg);
  border-radius: 0.25rem;
}
</style>
