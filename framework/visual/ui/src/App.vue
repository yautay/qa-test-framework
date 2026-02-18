<template>
  <div>
    <div class="d-flex align-items-center justify-content-between mb-3">
      <div>
        <h3 class="mb-0">Visual Regression Report</h3>
        <div class="text-muted small">Modal + zoom + slider (REF↔TEST)</div>
      </div>
      <div class="d-flex align-items-center gap-2">
        <div class="btn-group btn-group-sm" role="group" aria-label="tag persistence">
          <button type="button" class="btn btn-outline-secondary" @click="triggerTagImport">Import tags</button>
          <button type="button" class="btn btn-outline-secondary" @click="exportTags">Export tags</button>
          <button type="button" class="btn btn-outline-secondary" @click="syncTagsToFile">Sync tags</button>
        </div>
        <input
          ref="tagFileInput"
          type="file"
          accept="application/json"
          class="d-none"
          @change="onTagFileSelected"
        />
        <div v-if="tagSyncMessage" class="text-muted small">{{ tagSyncMessage }}</div>
        <div class="text-muted small mono">{{ store.summary }}</div>
      </div>
    </div>

    <FiltersPanel :store="store" @reset="reset" />
    <ResultsTable :rows="rows" :fmt="fmt" :tag-log="viewer.tagLog" :tag-key-for-row="getRowTagKey" @show="show" />
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
import FiltersPanel from "./components/FiltersPanel.vue";
import ResultsTable from "./components/ResultsTable.vue";
import ViewerModal from "./components/ViewerModal.vue";
import { fmt } from "./lib/format";
import { createStore, filteredSorted, resetFilters } from "./lib/store";
import {
  loadTagSnapshot,
  persistTagSnapshot,
  downloadTagSnapshot,
  parseTagFile,
  saveTagSnapshotToFile,
} from "./lib/tagPersistence";
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
} from "./lib/viewer";

export default {
  name: "VisualReportApp",
  components: {
    FiltersPanel,
    ResultsTable,
    ViewerModal,
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
  },
  methods: {
    fmt,
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
    reset() {
      resetFilters(this.store);
    },
    show(row, mode, index = null) {
      const fallbackMode = this.viewer.viewerMode || "test";
      const normalizedMode = mode === "compare" ? fallbackMode : (mode || fallbackMode);
      openViewer(this.viewer, row, normalizedMode, index);
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
    handleKeydown(evt) {
      const modalEl = document.getElementById("vrtModal");
      const isOpen = modalEl && modalEl.classList.contains("show");
      if (!isOpen) return;

      if (this.prompt.active) {
        if (evt.code === "Space") {
          this.confirmPrompt();
        } else if (evt.code === "ShiftLeft") {
          this.cancelPrompt();
        }
        return;
      }

      const k = evt.key;

      if (["1","2","3","4"].includes(k)) {
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
      } else if (evt.code === "ShiftLeft") {
        this.closeModal();
      } else if (k === "Escape") {
        this.viewer.modal?.hide();
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
  mounted() {
    window.addEventListener("keydown", this.handleKeydown);
    window.addEventListener("keyup", this.handleKeyup);
    this.loadTags();
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
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 0.75rem;
    background: #fff;
    padding: 0.5rem 0.75rem 0.25rem;
    display: flex;
    flex-direction: column;
    min-height: 220px;
    position: relative;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }
  .slot-divider {
    height: 1px;
    background: rgba(0,0,0,0.08);
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
    background: #fff;
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
    color: #6c757d;
    font-size: 0.85rem;
  }
</style>
