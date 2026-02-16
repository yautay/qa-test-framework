import { fmt } from "./format.js";
import { createStore, filteredSorted, resetFilters } from "./store.js";
import {
  createViewerState, ensureModal, openViewer, setMode,
  zoomIn, zoomOut, resetZoom, onWheelZoom,
  panStart, panMove, panEnd,
  toggleFit
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
            <tr v-for="r in rows" :key="r.scenario_id">
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
                  <button v-if="r.baseline_path" class="btn btn-sm btn-outline-primary" @click="show(r,'ref')">ref</button>
                  <button v-if="r.actual_path" class="btn btn-sm btn-outline-primary" @click="show(r,'test')">test</button>
                  <button v-if="r.diff_path" class="btn btn-sm btn-outline-primary" @click="show(r,'diff')">pixel_diff</button>
                  <button v-if="r.heatmap_path" class="btn btn-sm btn-outline-primary" @click="show(r,'lpips')">lpips</button>
                  <button v-if="r.baseline_path && r.actual_path" class="btn btn-sm btn-outline-success" @click="show(r,'compare')">compare</button>
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
      <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <div class="mono fw-semibold">{{ viewer.modalTitle }}</div>
              <div class="text-muted small mono">{{ viewer.modalSubtitle }}</div>
              <div class="text-muted small mono">
                shortcuts: 1-5 modes, +/- zoom, 0 reset, ←/→ slider, Esc close, F fit
              </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>

          <div class="modal-body">

            <!-- toolbar -->
            <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
              <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-secondary" @click="mode('ref')" :disabled="!viewer.modalRefSrc">REF</button>
                <button class="btn btn-outline-secondary" @click="mode('test')" :disabled="!viewer.modalTestSrc">TEST</button>
                <button class="btn btn-outline-secondary" @click="mode('diff')" :disabled="!viewer.modalDiffSrc">PIXEL_DIFF</button>
                <button class="btn btn-outline-secondary" @click="mode('lpips')" :disabled="!viewer.modalLpipsSrc">LPIPS</button>
                <button class="btn btn-outline-secondary" @click="mode('compare')" :disabled="!(viewer.modalRefSrc && viewer.modalTestSrc)">COMPARE</button>
              </div>

              <div class="btn-group btn-group-sm ms-2">
                <button class="btn btn-outline-secondary" @click="zOut()">-</button>
                <button class="btn btn-outline-secondary" @click="zReset()">reset</button>
                <button class="btn btn-outline-secondary" @click="zIn()">+</button>
                <button class="btn btn-outline-secondary" @click="toggleFitMode()">
                  {{ viewer.fitMode ? 'FIT' : '1:1' }}
                </button>
              </div>

              <div class="text-muted small mono">zoom={{ viewer.zoom.toFixed(2) }}x</div>

              <div v-if="viewer.viewerMode==='compare'" class="ms-auto d-flex align-items-center gap-2">
                <div class="text-muted small mono">REF</div>
                <input type="range" class="form-range" style="width: 260px"
                       v-model.number="viewer.slider" min="0" max="100" />
                <div class="text-muted small mono">TEST</div>
              </div>
            </div>

            <!-- viewer area -->
            <div class="border rounded overflow-auto bg-white"
                 style="min-height: 520px;"
                 @wheel.passive="wheel"
                 @mousedown="panStartHandler"
                 @mousemove="panMoveHandler"
                 @mouseup="panEndHandler"
                 @mouseleave="panEndHandler"
                 @dblclick="zReset">

              <!-- compare -->
              <div v-if="viewer.viewerMode==='compare'" class="position-relative"
                   :style="transformStyle">
                <img :src="viewer.modalTestSrc" class="d-block"
                     :style="{ width: viewer.fitMode ? '100%' : 'auto', height: 'auto' }" />
                <div class="position-absolute top-0 start-0 overflow-hidden"
                     :style="{ width: viewer.slider + '%', height: '100%' }">
                  <img :src="viewer.modalRefSrc" class="d-block"
                       :style="{ width: viewer.fitMode ? '100%' : 'auto', height: 'auto' }" />
                </div>
                <div class="position-absolute top-0"
                     :style="{ left: viewer.slider + '%', height: '100%', width: '2px', background: '#0d6efd' }"></div>
              </div>

              <!-- single -->
              <div v-else class="p-2" :style="transformStyle">
                <img v-if="viewer.modalImgSrc" :src="viewer.modalImgSrc" class="d-block"
                     :style="{ maxWidth: viewer.fitMode ? '100%' : 'none', height: 'auto' }" />
                <div v-else class="text-muted p-4">Brak obrazu.</div>
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
    };
  },
  computed: {
    rows() {
      return filteredSorted(this.store);
    },
    transformStyle() {
      return {
        transform: `translate(${this.viewer.panX}px, ${this.viewer.panY}px) scale(${this.viewer.zoom})`,
        transformOrigin: "top left",
        cursor: this.viewer.isPanning ? "grabbing" : "grab",
      };
    }
  },
  methods: {
    fmt,
    reset() { resetFilters(this.store); },

    show(row, mode) {
      openViewer(this.viewer, row, mode);
      ensureModal(this.viewer, "vrtModal").show();
    },
    mode(mode) {
      setMode(this.viewer, mode);
    },

    toggleFitMode() {
      toggleFit(this.viewer);
    },

    zIn() { zoomIn(this.viewer); },
    zOut() { zoomOut(this.viewer); },
    zReset() { resetZoom(this.viewer); },

    wheel(evt) {
      // zoom tylko z CTRL — inaczej normalny scroll
      if (!evt.ctrlKey) return;
      onWheelZoom(this.viewer, evt);
    },

    panStartHandler(evt) {
      if (this.viewer.zoom <= 1) return;
      panStart(this.viewer, evt);
    },
    panMoveHandler(evt) { panMove(this.viewer, evt); },
    panEndHandler() { panEnd(this.viewer); },

    handleKeydown(evt) {
      // reaguj tylko gdy modal jest otwarty
      const modalEl = document.getElementById("vrtModal");
      const isOpen = modalEl && modalEl.classList.contains("show");
      if (!isOpen) return;

      const k = evt.key;

      if (k === "1") this.mode("ref");
      else if (k === "2") this.mode("test");
      else if (k === "3") this.mode("diff");
      else if (k === "4") this.mode("lpips");
      else if (k === "5") this.mode("compare");

      else if (k === "+" || k === "=") this.zIn();
      else if (k === "-") this.zOut();
      else if (k === "0") this.zReset();

      else if ((k === "f" || k === "F")) this.toggleFitMode();

      else if (k === "ArrowLeft" && this.viewer.viewerMode === "compare") {
        this.viewer.slider = Math.max(0, this.viewer.slider - 3);
        evt.preventDefault();
      } else if (k === "ArrowRight" && this.viewer.viewerMode === "compare") {
        this.viewer.slider = Math.min(100, this.viewer.slider + 3);
        evt.preventDefault();
      }

      else if (k === "Escape") {
        this.viewer.modal?.hide();
      }
    },
  },
  mounted() {
    window.addEventListener("keydown", this.handleKeydown);
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleKeydown);
  }
}).mount("#app");
