import { fmt } from "./format.js";
import { createStore, filteredSorted, resetFilters } from "./store.js";
import {
  createViewerState, ensureModal, openViewer,
  getAvailableModes, getModeSrc, refreshSlots,
  setPresentationMode, navigateRow,
  setCursorPosition, toggleTag, getRowTagKey
} from "./viewer.js";

const { createApp } = window.Vue;

createApp({
  template: `
  <div>
    <div class="d-flex align-items-center justify-content-between mb-3">
      <div>
        <h3 class="mb-0">Visual Regression Report</h3>
        <div class="text-muted small">Modal + zoom + slider (REF↔TEST)</div>
      </div>
      <div class="text-muted small mono">{{ store.summary }}</div>
    </div>

    <div class="card mb-3 shadow-sm">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-12 col-md-4">
            <label class="form-label">Szukaj (scenario/message)</label>
            <input class="form-control" v-model="store.q" placeholder="np. hero, header..." />
          </div>

          <div class="col-6 col-md-2">
            <label class="form-label">Status</label>
            <select class="form-select" v-model="store.status">
              <option value="">All</option>
              <option value="passed">passed</option>
              <option value="failed">failed</option>
              <option value="skipped">skipped</option>
              <option value="error">error</option>
              <option value="new">new</option>
            </select>
          </div>

          <div class="col-6 col-md-2">
            <label class="form-label">Mode</label>
            <select class="form-select" v-model="store.mode">
              <option value="">All</option>
              <option value="pixel">pixel</option>
              <option value="perceptual">perceptual</option>
              <option value="hybrid">hybrid</option>
            </select>
          </div>

          <div class="col-6 col-md-2">
            <label class="form-label">Sort</label>
            <select class="form-select" v-model="store.sortKey">
              <option value="scenario_id">scenario_id</option>
              <option value="status">status</option>
              <option value="pixel_changed_ratio">pixel</option>
              <option value="lpips">lpips</option>
              <option value="dists">dists</option>
            </select>
          </div>

          <div class="col-6 col-md-2">
            <label class="form-label">&nbsp;</label>
            <button class="btn btn-outline-secondary w-100" @click="reset()">Reset</button>
          </div>
        </div>
      </div>
    </div>

    <div class="card shadow-sm">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>Scenario</th>
              <th class="small-col">Status</th>
              <th class="small-col">Mode</th>
              <th class="small-col">Pixel</th>
              <th class="small-col">LPIPS</th>
              <th class="small-col">DISTS</th>
              <th>Message</th>
              <th>Artifacts</th>
            </tr>
          </thead>
            <tbody>
             <tr v-for="(r, index) in rows" :key="r.scenario_id">
              <td class="mono">{{ r.scenario_id }}</td>

              <td class="small-col">
                <span class="badge"
                  :class="{
                    'text-bg-success': r.status==='passed',
                    'text-bg-danger': r.status==='failed',
                    'text-bg-warning': r.status==='skipped' || r.status==='new',
                    'text-bg-dark': r.status==='error'
                  }">{{ r.status }}</span>
              </td>

              <td class="small-col"><span class="badge text-bg-secondary">{{ r.compare_mode }}</span></td>
              <td class="small-col mono">{{ fmt(r.pixel_changed_ratio) }}</td>
              <td class="small-col mono">{{ fmt(r.lpips) }}</td>
              <td class="small-col mono">{{ fmt(r.dists) }}</td>
              <td style="max-width: 420px;">{{ r.message || '' }}</td>

              <td style="min-width: 430px;">
                <div class="d-flex flex-wrap gap-2">
                  <button v-if="r.baseline_path" class="btn btn-sm btn-outline-primary" @click="show(r,'ref', index)">ref</button>
                  <button v-if="r.actual_path" class="btn btn-sm btn-outline-primary" @click="show(r,'test', index)">test</button>
                  <button v-if="r.diff_path" class="btn btn-sm btn-outline-primary" @click="show(r,'diff', index)">pixel_diff</button>
                  <button v-if="r.heatmap_path" class="btn btn-sm btn-outline-primary" @click="show(r,'lpips', index)">lpips</button>
                  <button v-if="r.baseline_path && r.actual_path" class="btn btn-sm btn-outline-success" @click="show(r,'compare', index)">compare</button>
                </div>
              </td>
            </tr>

            <tr v-if="rows.length===0">
              <td colspan="8" class="text-center text-muted py-4">Brak wyników dla filtrów.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="vrtModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable modal-full">
        <div class="modal-content">
          <div class="modal-header justify-content-between align-items-start">
            <div>
              <div class="mono fw-semibold">{{ viewer.modalTitle }}</div>
              <div class="text-muted small mono">{{ viewer.modalSubtitle }}</div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>

          <div class="modal-body d-flex flex-column" ref="modalBody"
               @mousemove="handleMouseMove"
               @mouseleave="resetCursor">

            <div class="d-flex flex-wrap gap-2 align-items-center mb-3 toolbar">
              <div class="btn-group btn-group-sm" role="group">
                <button v-for="count in [1,2,3,4]" :key="count"
                        type="button"
                        class="btn"
                        :class="viewer.columns===count ? 'btn-primary' : 'btn-outline-secondary'"
                        @click="setColumns(count)">
                  {{ count }}
                </button>
              </div>

              <select class="form-select form-select-sm" v-model="viewer.presentationMode" @change="handlePresentation">
                <option v-for="mode in modalModes" :key="mode.value" :value="mode.value" :disabled="!mode.available">
                  {{ mode.label }}
                </option>
              </select>

              <div class="btn-group btn-group-sm" role="group">
                <button type="button" class="btn" :class="keyHeld.a ? 'btn-primary' : 'btn-outline-secondary'" @mousedown="keyHeld.a=true" @mouseup="keyHeld.a=false" @click="navigate(-1)">← K-A</button>
                <button type="button" class="btn" :class="keyHeld.d ? 'btn-primary' : 'btn-outline-secondary'" @mousedown="keyHeld.d=true" @mouseup="keyHeld.d=false" @click="navigate(1)">K-D →</button>
              </div>

              <div class="btn-group btn-group-sm" role="group">
                <button type="button" class="btn" :class="zoomClass(30)" @mousedown.prevent="handleZoomMouse(30,$event)" @mouseup.prevent="clearZoomMouse" @mouseleave.prevent="clearZoomMouse">> K-Q</button>
                <button type="button" class="btn" :class="middleZoomClass()" @click="clearZoomMouse">O</button>
                <button type="button" class="btn" :class="zoomClass(90)" @mousedown.prevent="handleZoomMouse(90,$event)" @mouseup.prevent="clearZoomMouse" @mouseleave.prevent="clearZoomMouse">< K-E</button>
              </div>
              <div class="btn-group btn-group-sm fit-group" role="group">
                <button v-for="fit in fitModes" :key="fit.key" type="button"
                        class="btn"
                        :class="presentationFit===fit.key ? 'btn-primary' : 'btn-outline-secondary'"
                        @click="setPresentationFit(fit.key)">
                  {{ fit.label }}
                </button>
              </div>
              <button type="button" :class="superZoomActive ? 'btn btn-primary ms-1' : 'btn btn-outline-secondary ms-1'" @mousedown.prevent="activateSuperZoom" @mouseup.prevent="deactivateSuperZoom" @mouseleave.prevent="deactivateSuperZoom">🔍 K-W</button>

               <div class="btn-group btn-group-sm" role="group">
                 <button v-if="!viewer.tags.bug" type="button" class="btn btn-outline-danger" @click="promptTag('bug')">BUG! (K-S)</button>
                 <button v-if="!viewer.tags.aso" type="button" class="btn btn-outline-warning text-dark" @click="promptTag('aso')">ASO (K-C)</button>
               </div>

              <button type="button" class="btn btn-outline-secondary btn-sm ms-auto" @click="closeModal">Exit (K-LSHIFT)</button>
            </div>

              <div class="text-muted small mb-2">Keys: 1‑4 layout, A/D navigate, hold Q/E zoom, hold W super zoom, S/C tags prompt, Shift = exit</div>

            <div class="flex-grow-1 overflow-auto pb-2 position-relative">
              <div class="slot-grid" :style="gridStyle">
                <div v-for="slot in viewer.slots" :key="slot.id" class="slot-card">
                  <div class="slot-header d-flex justify-content-between align-items-center">
                    <div class="mono small">Slot {{ slot.id }}</div>
                    <div class="d-flex gap-1">
                      <span v-if="viewer.tags.bug" class="badge bg-danger">BUG</span>
                      <span v-if="viewer.tags.aso" class="badge bg-warning text-dark">ASO</span>
                    </div>
                  </div>
                  <div class="slot-divider"></div>
                  <div class="slot-media">
                    <img v-if="slotImage(slot)" :src="slotImage(slot)"
                         class="w-100 h-100"
                         :style="[presentationStyle, imageStyle]" />
                    <div v-else class="text-muted small text-center position-absolute top-50 start-50 translate-middle">
                      Brak obrazu dla {{ viewer.presentationMode }}
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="prompt.active" class="prompt-overlay">
                <div class="prompt-card">
                  <div class="prompt-title">Potwierdzenie</div>
                  <div class="prompt-text">Czy na pewno oznaczyć to jako {{ prompt.type === 'bug' ? 'BUG' : 'ASO' }}?</div>
                  <div class="prompt-hints">Space = TAK &nbsp;•&nbsp; Shift = NIE</div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>

  </div>
  `,
  data() {
    return {
      store: createStore(),
      viewer: createViewerState(),
      baseZoom: 160,
      zoomDelta: 0,
      storedDelta: 0,
      superZoomActive: false,
      keyHeld: { a: false, d: false, q: false, e: false, w: false, s: false, c: false },
      prompt: { active: false, type: null },
      presentationFit: "FIT",
    };
  },
  computed: {
    rows() {
      return filteredSorted(this.store);
    },
    modalModes() {
      return getAvailableModes(this.viewer);
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
      const level = this.superZoomActive ? this.baseZoom + 200 : this.baseZoom + this.zoomDelta;
      return level / 100;
    },
    fitModes() {
      return [
        { key: "FIT", label: "FIT" },
        { key: "VERT", label: "VERT" },
        { key: "HORIZ", label: "HORIZ" },
        { key: "CENTER", label: "CENTER" },
      ];
    },
    presentationStyle() {
      const mode = this.presentationFit;
      const style = {
        width: "100%",
        height: "100%",
        objectFit: "contain",
        objectPosition: "center",
      };
      if (mode === "VERT") {
        style.width = "auto";
        style.height = "100%";
      } else if (mode === "HORIZ") {
        style.width = "100%";
        style.height = "auto";
      }
      return style;
    },
  },
  methods: {
    fmt,
    reset() { resetFilters(this.store); },

    show(row, mode, index = null) {
      const fallbackMode = this.viewer.presentationMode || "test";
      const normalizedMode = mode === "compare" ? fallbackMode : (mode || fallbackMode);
      setPresentationMode(this.viewer, normalizedMode);
      openViewer(this.viewer, row, normalizedMode, index);
      ensureModal(this.viewer, "vrtModal").show();
    },
    slotImage(_slot) {
      return getModeSrc(this.viewer, this.viewer.presentationMode) || this.viewer.modalImgSrc;
    },
    imageStyle() {
      const scale = this.zoomScale;
      return {
        transform: `scale(${scale})`,
        transformOrigin: `${this.viewer.cursorX}% ${this.viewer.cursorY}%`,
      };
    },
    handlePresentation(evt) {
      setPresentationMode(this.viewer, evt.target.value);
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
      } else if (k.toUpperCase() === "Q") {
        this.keyHeld.q = true;
        this.startDelta(30);
      } else if (k.toUpperCase() === "E") {
        this.keyHeld.e = true;
        this.startDelta(90);
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
      if (k.toUpperCase() === "Q") {
        this.keyHeld.q = false;
        this.resetDelta();
      }
      if (k.toUpperCase() === "E") {
        this.keyHeld.e = false;
        this.resetDelta();
      }
      if (k.toUpperCase() === "W") {
        this.keyHeld.w = false;
        this.deactivateSuperZoom();
      }
    },
    setZoomDelta(value) {
      this.zoomDelta = value;
    },
    startDelta(value) {
      this.storedDelta = this.zoomDelta;
      this.setZoomDelta(value);
    },
    resetDelta() {
      this.setZoomDelta(this.storedDelta);
      this.storedDelta = 0;
    },
    zoomClass(value) {
      return this.zoomDelta === value && !this.superZoomActive ? 'btn-primary' : 'btn-outline-secondary';
    },
    middleZoomClass() {
      return this.zoomDelta === 0 && !this.superZoomActive ? 'btn-primary' : 'btn-outline-secondary';
    },
    handleZoomMouse(value, evt) {
      if (evt.button !== 0) return;
      this.startDelta(value);
    },
    clearZoomMouse() {
      this.resetDelta();
    },
    activateSuperZoom() {
      this.superZoomActive = true;
      this.storedDelta = this.zoomDelta;
      this.zoomDelta = 200;
    },
    deactivateSuperZoom() {
      this.superZoomActive = false;
      this.zoomDelta = this.storedDelta;
      this.storedDelta = 0;
    },
    navigate(offset) {
      const next = navigateRow(this.viewer, this.rows, offset);
      if (next) {
        this.show(next.row, this.viewer.presentationMode, next.index);
      }
    },
    isTagLocked(type) {
      const row = this.viewer.modalRow;
      if (!row) return false;
      const key = getRowTagKey(row);
      return !!this.viewer.tagLocked?.[key]?.[type];
    },
    promptTag(type) {
      if (this.prompt.active) return;
      if (this.isTagLocked(type)) return;
      this.prompt = { active: true, type };
    },
    setPresentationFit(mode) {
      this.presentationFit = mode;
      const base = this.computeBaseZoom();
      this.baseZoom = base;
      if (!this.superZoomActive) {
        this.zoomDelta = 0;
      }
    },
    computeBaseZoom() {
      switch (this.presentationFit) {
        case "VERT":
          return 170;
        case "HORIZ":
          return 170;
        case "CENTER":
          return 192;
        default:
          return 160;
      }
    },
    confirmPrompt() {
      if (!this.prompt.active) return;
      toggleTag(this.viewer, this.viewer.modalRow, this.prompt.type);
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
    handleMouseMove(evt) {
      const body = this.$refs.modalBody;
      if (!body) return;
      setCursorPosition(this.viewer, body.getBoundingClientRect(), evt);
    },
    resetCursor() {
      this.viewer.cursorX = 50;
      this.viewer.cursorY = 50;
    },
  },
  mounted() {
    window.addEventListener("keydown", this.handleKeydown);
    window.addEventListener("keyup", this.handleKeyup);
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleKeydown);
    window.removeEventListener("keyup", this.handleKeyup);
  }
}).mount("#app");
