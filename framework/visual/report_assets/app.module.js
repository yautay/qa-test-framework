import { fmt } from "./format.js";
import { createStore, filteredSorted, resetFilters } from "./store.js";
import {
  createViewerState, ensureModal, openViewer,
  getAvailableModes, getModeSrc, refreshSlots
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
      <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable modal-full">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <div class="mono fw-semibold">{{ viewer.modalTitle }}</div>
              <div class="text-muted small mono">{{ viewer.modalSubtitle }}</div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>

          <div class="modal-body">

            <div class="d-flex flex-wrap gap-3 align-items-center mb-3">
              <div class="d-flex align-items-center gap-2">
                <span class="text-muted small">Zdjęć w wierszu:</span>
                <div class="btn-group btn-group-sm">
                  <button v-for="count in [1,2,3,4]" :key="count"
                          class="btn"
                          :class="viewer.columns===count ? 'btn-primary' : 'btn-outline-secondary'"
                          @click="setColumns(count)">
                    {{ count }}
                  </button>
                </div>
              </div>
              <div class="text-muted small mono ms-auto">Każdy slot wybiera REF/TEST/HEAT.</div>
            </div>

            <div class="flex-grow-1 overflow-auto pb-2">
              <div class="d-grid gap-3" :style="gridStyle">
                <div v-for="slot in viewer.slots" :key="slot.id" class="card h-100 shadow-sm">
                  <div class="card-body d-flex flex-column gap-2">
                    <div class="d-flex gap-2 align-items-center justify-content-between">
                      <div class="mono small text-muted">Slot {{ slot.id }}</div>
                      <select class="form-select form-select-sm w-auto" v-model="slot.mode">
                        <option v-for="mode in modalModes" :key="mode.value" :value="mode.value" :disabled="!mode.available">
                          {{ mode.label }}
                        </option>
                      </select>
                    </div>
                    <div class="border rounded bg-white flex-grow-1 position-relative overflow-hidden" style="min-height: 210px;">
                      <img v-if="slotImage(slot)" :src="slotImage(slot)" class="d-block w-100 h-100" style="object-fit: contain;" />
                      <div v-else class="text-muted small text-center position-absolute top-50 start-50 translate-middle">
                        Brak obrazu dla {{ modeLabel(slot.mode) || 'wybranego rodzaju' }}
                      </div>
                    </div>
                  </div>
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
        gridAutoRows: "1fr",
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
    slotImage(slot) {
      return getModeSrc(this.viewer, slot.mode);
    },
    modeLabel(value) {
      return this.modalModes.find((mode) => mode.value === value)?.label;
    },
    setColumns(value) {
      this.viewer.columns = value;
      refreshSlots(this.viewer, value);
    },
    handleKeydown(evt) {
      if (evt.key !== "Escape") return;
      const modalEl = document.getElementById("vrtModal");
      if (modalEl && modalEl.classList.contains("show")) {
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
