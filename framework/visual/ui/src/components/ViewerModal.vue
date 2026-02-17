<template>
  <div class="modal fade" id="vrtModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-fullscreen modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header justify-content-between align-items-start">
          <div>
            <div class="mono fw-semibold">{{ viewer.modalTitle }}</div>
            <div class="text-muted small mono">{{ viewer.modalSubtitle }}</div>
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
              <button v-if="!viewer.tags.bug" type="button" class="btn btn-outline-danger" @click="$emit('prompt-tag','bug')">BUG! (K-S)</button>
              <button v-if="!viewer.tags.aso" type="button" class="btn btn-outline-warning text-dark" @click="$emit('prompt-tag','aso')">ASO (K-C)</button>
            </div>

            <button type="button" class="btn btn-outline-secondary btn-sm ms-auto" @click="$emit('close-modal')">Exit (K-LSHIFT)</button>
          </div>

          <div class="text-muted small mb-2">Keys: 1‑4 layout, A/D navigate, hold W super zoom, S/C tags prompt, Shift = exit</div>

          <div class="flex-grow-1 overflow-auto pb-2 position-relative">
            <div class="slot-grid" :style="gridStyle">
              <div v-for="slot in viewer.slots" :key="slot.id" class="slot-card">
                <div class="slot-header d-flex justify-content-between align-items-center">
                  <div class="mono small">Slot {{ slot.id }}</div>
                  <div class="d-flex align-items-center gap-2">
                    <select class="form-select form-select-sm slot-mode-select"
                            :value="slot.mode"
                            @change="$emit('set-slot-mode', slot.id, $event.target.value)">
                      <option v-for="mode in modeOptions" :key="mode.value" :value="mode.value">
                        {{ mode.label }}
                      </option>
                    </select>
                    <div class="d-flex gap-1">
                      <span v-if="viewer.tags.bug" class="badge bg-danger">BUG</span>
                      <span v-if="viewer.tags.aso" class="badge bg-warning text-dark">ASO</span>
                    </div>
                  </div>
                </div>
                <div class="slot-divider"></div>
                <div class="slot-media">
                  <img v-if="slotImage(slot)" :src="slotImage(slot)"
                       :style="[presentationStyle, imageStyle]" />
                  <div v-else class="text-muted small text-center position-absolute top-50 start-50 translate-middle">
                    Brak obrazu dla {{ slotModeLabel(slot.mode) }}
                  </div>
                </div>
              </div>
            </div>

            <div v-if="prompt.active" class="prompt-overlay">
              <div class="prompt-card">
                <div class="prompt-title">Potwierdzenie</div>
                <div class="prompt-text">Czy na pewno oznaczyć to jako {{ prompt.type === 'bug' ? 'BUG' : 'ASO' }}?</div>
                <div class="prompt-hints">Shift = NIE &nbsp;•&nbsp; Space = TAK</div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script>
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
    "close-modal",
    "reset-cursor",
    "mouse-move",
  ],
  computed: {
    modeOptions() {
      return [
        { value: "ref", label: "REF" },
        { value: "test", label: "TEST" },
        { value: "diff", label: "DIFF" },
        { value: "lpips", label: "PERC" },
      ];
    },
  },
  methods: {
    onMouseMove(evt) {
      const bounds = evt.currentTarget?.getBoundingClientRect();
      this.$emit('mouse-move', { bounds, evt });
    },
    slotModeLabel(mode) {
      const match = this.modeOptions.find((item) => item.value === mode);
      return match ? match.label : "";
    },
  },
};
</script>
