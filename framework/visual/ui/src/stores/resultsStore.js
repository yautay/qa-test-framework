import { defineStore } from "pinia";
import { summaryFor } from "../lib/format";
import { normalizeCaseStateSnapshot } from "../lib/notes";
import { getRowTagKey } from "../lib/viewer";

const NUMERIC_SORT_KEYS = ["pixel_changed_ratio", "lpips", "dists"];

const STATUS_PRIORITY = {
  failed: 0,
  skipped: 1,
  passed: 2,
};

const TAG_PRIORITY = {
  bug: 0,
  aso: 1,
  baseline: 2,
};

const DEFAULT_SLOT_COUNT = 2;

const SLOT_MODE_DEFAULTS = {
  1: "ref",
  2: "test",
  3: "diff",
  4: "lpips",
};

const EMPTY_TAG_ENTRY = {
  bug: { locked: false, synced: false },
  aso: { locked: false, synced: false },
  note: { content: "", synced: false },
  baseline: false,
};

function buildEmptyTagEntry() {
  return {
    bug: { ...EMPTY_TAG_ENTRY.bug },
    aso: { ...EMPTY_TAG_ENTRY.aso },
    note: { ...EMPTY_TAG_ENTRY.note },
    baseline: EMPTY_TAG_ENTRY.baseline,
  };
}

function compareValues(av, bv, key) {
  if (av == null && bv == null) return 0;
  if (av == null) return 1;
  if (bv == null) return -1;

  if (key === "status") {
    const aPriority = STATUS_PRIORITY[av] ?? 99;
    const bPriority = STATUS_PRIORITY[bv] ?? 99;
    return aPriority - bPriority;
  }

  if (NUMERIC_SORT_KEYS.includes(key)) {
    return Number(bv) - Number(av);
  }

  return String(av).localeCompare(String(bv));
}

function getTagPriority(row, tagLog) {
  const key = getRowTagKey(row);
  const tags = tagLog?.[key];
  if (!tags) return 3;
  if (tags.bug?.locked) return TAG_PRIORITY.bug;
  if (tags.aso?.locked) return TAG_PRIORITY.aso;
  if (tags.baseline) return TAG_PRIORITY.baseline;
  return 3;
}

function hasRowNote(row, tagLog) {
  const key = getRowTagKey(row);
  const text = tagLog?.[key]?.note?.content;
  return typeof text === "string" && !!text.trim();
}

function defaultSlotMode(slotId) {
  return SLOT_MODE_DEFAULTS[slotId] || "test";
}

function buildSlots(slotCount, existingSlots, existingModes) {
  const count = Math.max(1, slotCount);
  const existing = new Map((existingSlots || []).map((slot) => [slot.id, slot]));
  const slotModes = existingModes || {};
  return Array.from({ length: count }, (_, idx) => {
    const id = idx + 1;
    const previous = existing.get(id);
    const mode = slotModes[id] || previous?.mode || defaultSlotMode(id);
    slotModes[id] = mode;
    return { id, mode };
  });
}

export const useResultsStore = defineStore("results", {
  state: () => ({
    rows: [],
    q: "",
    status: "",
    viewport: "",
    browser: "",
    sortKey: "scenario_id",
    summary: summaryFor([]),

    runId: "",
    modalOpen: false,
    viewerMode: "test",
    modalRow: null,
    modalTitle: "",
    modalSubtitle: "",
    columns: DEFAULT_SLOT_COUNT,
    cursorX: 50,
    cursorY: 50,
    currentIndex: null,
    slots: [],
    slotModes: { 1: "ref", 2: "test", 3: "diff", 4: "lpips" },
    tagLog: {},

    selectedIndex: -1,
    loadError: "",
  }),

  getters: {
    filteredSorted: (state) => {
      const tagLog = state.tagLog;
      const q = state.q.trim().toLowerCase();
      let out = [...state.rows];

      if (state.status === "with_note") {
        out = out.filter((r) => hasRowNote(r, tagLog));
      } else if (state.status) {
        out = out.filter((r) => r.status === state.status);
      }
      if (state.viewport) out = out.filter((r) => r.viewport === state.viewport);
      if (state.browser) out = out.filter((r) => r.browser === state.browser);

      if (q) {
        out = out.filter(
          (r) =>
            (r.scenario_id || "").toLowerCase().includes(q) ||
            (r.message || "").toLowerCase().includes(q)
        );
      }

      const key = state.sortKey;

      if (key === "tags") {
        out = [...out].sort((a, b) => {
          const aPriority = getTagPriority(a, tagLog);
          const bPriority = getTagPriority(b, tagLog);
          if (aPriority !== bPriority) return aPriority - bPriority;
          return String(a.scenario_id || "").localeCompare(String(b.scenario_id || ""));
        });
        return out;
      }

      if (key === "note") {
        out = [...out].sort((a, b) => {
          const aHasNote = hasRowNote(a, tagLog);
          const bHasNote = hasRowNote(b, tagLog);
          if (aHasNote !== bHasNote) {
            return aHasNote ? -1 : 1;
          }
          return String(a.scenario_id || "").localeCompare(String(b.scenario_id || ""));
        });
        return out;
      }

      out = [...out].sort((a, b) => compareValues(a[key], b[key], key));
      return out;
    },

    summaryText: (state) => {
      const summary = state.summary || {};
      const total = Number(summary.total || 0);
      const passed = Number(summary.passed || 0);
      const failed = Number(summary.failed || 0);
      const skipped = Number(summary.skipped || 0);
      const uncertain = Number(summary.uncertain || 0);
      const base = `total=${total} passed=${passed} failed=${failed} skipped=${skipped}`;
      return uncertain ? `${base} uncertain=${uncertain}` : base;
    },

    gridStyle: (state) => {
      const requested = Math.max(1, state.columns || 1);
      const columns = requested === 4 ? 2 : requested;
      return {
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
        alignContent: requested === 4 ? "center" : "start",
        gridAutoRows: "1fr",
      };
    },

    viewports: (state) => {
      const vps = new Set();
      for (const row of state.rows || []) {
        if (row.viewport) vps.add(row.viewport);
      }
      return Array.from(vps).sort();
    },

    browsers: (state) => {
      const items = new Set();
      for (const row of state.rows || []) {
        if (row.browser) items.add(row.browser);
      }
      return Array.from(items).sort();
    },

    filtersActive: (state) => {
      return (
        !!state.q.trim() ||
        !!state.status ||
        !!state.viewport ||
        !!state.browser
      );
    },

    baselineCandidates: (state) => {
      return state.rows.filter((row) => {
        const key = getRowTagKey(row);
        const tags = state.tagLog?.[key];
        return !!(tags?.baseline && row?.actual_path);
      });
    },

    reportCandidatesCount: (state) => {
      return state.rows.reduce((count, row) => {
        const key = getRowTagKey(row);
        const tags = state.tagLog?.[key] || {};
        const canSendBug = !!tags.bug?.locked && !tags.bug?.synced;
        const canSendAso = !!tags.aso?.locked && !tags.aso?.synced;

        const noteText = tags.note?.content || "";
        const noteHasText = typeof noteText === "string" && noteText.trim() !== "";
        const canSendNote = noteHasText && !tags.note?.synced;

        return count + (canSendBug || canSendAso || canSendNote ? 1 : 0);
      }, 0);
    },

    hasAnyBug: (state) => {
      return state.rows.reduce((count, row) => {
        const key = getRowTagKey(row);
        const tags = state.tagLog?.[key];
        return count + (tags?.bug?.locked ? 1 : 0);
      }, 0);
    },

    currentTagKey: (state) => {
      return state.modalRow ? getRowTagKey(state.modalRow) : "";
    },

    currentTags: (state) => {
      if (!state.modalRow) return buildEmptyTagEntry();
      const key = getRowTagKey(state.modalRow);
      return state.tagLog?.[key] || buildEmptyTagEntry();
    },
  },

  actions: {
    setRows(rows) {
      const normalized = Array.isArray(rows)
        ? rows.map((row) => {
            if (!row || typeof row !== "object") return row;
            const status = row.status === "new" ? "failed" : row.status;
            return { ...row, status };
          })
        : [];
      this.rows = normalized;
      this.summary = summaryFor(normalized);
    },

    setFilter(key, value) {
      if (key in this) {
        this[key] = value;
      }
    },

    resetFilters() {
      this.q = "";
      this.status = "";
      this.viewport = "";
      this.browser = "";
      this.sortKey = "scenario_id";
    },

    setRunId(runId) {
      this.runId = runId;
    },

    openViewer(row, mode, index = null) {
      const runId = this.runId;
      this.modalRow = row;
      this.modalOpen = true;

      this.modalTitle = row.scenario_id || "";
      this.modalSubtitle = `status=${row.status || ""} mode=${row.compare_mode || ""}`;

      if (mode === "ref" || mode === "test" || mode === "diff" || mode === "lpips") {
        this.viewerMode = mode;
      } else {
        this.viewerMode = "test";
      }

      this.slots = buildSlots(this.columns, this.slots, this.slotModes);
      this.currentIndex = index;
    },

    closeViewer() {
      this.modalOpen = false;
      this.modalRow = null;
      this.cursorX = 50;
      this.cursorY = 50;
    },

    setColumns(value) {
      this.columns = value;
      this.slots = buildSlots(this.columns, this.slots, this.slotModes);
    },

    setSlotMode(slotId, mode) {
      const slot = this.slots.find((item) => item.id === slotId);
      if (!slot) return;
      slot.mode = mode;
      this.slotModes[slotId] = mode;
    },

    toggleBaseline() {
      if (!this.modalRow) return;
      const key = getRowTagKey(this.modalRow);
      const existing = this.tagLog[key] ? { ...this.tagLog[key] } : buildEmptyTagEntry();
      existing.baseline = !existing.baseline;
      this.tagLog[key] = existing;
    },

    setBaseline(value) {
      if (!this.modalRow) return;
      const key = getRowTagKey(this.modalRow);
      const existing = this.tagLog[key] ? { ...this.tagLog[key] } : buildEmptyTagEntry();
      existing.baseline = !!value;
      this.tagLog[key] = existing;
    },

    isTagLocked(type) {
      const tags = this.currentTags;
      if (type === "bug") return !!tags.bug?.locked;
      if (type === "aso") return !!tags.aso?.locked;
      if (type === "baseline") return !!tags.baseline;
      return false;
    },

    isTagReported(type) {
      if (!this.modalRow) return false;
      const tags = this.currentTags || {};
      if (type === "bug") return !!tags.bug?.synced;
      if (type === "aso") return !!tags.aso?.synced;
      if (type === "note") return !!tags.note?.synced;
      return false;
    },

    updateTagLog(snapshot) {
      if (!snapshot || typeof snapshot !== "object") {
        this.tagLog = {};
        return;
      }
      const normalized = normalizeCaseStateSnapshot(snapshot);
      const merged = {};
      for (const [key, value] of Object.entries(normalized)) {
        const baseline = this.tagLog?.[key]?.baseline || false;
        merged[key] = { ...value, baseline };
      }
      for (const [key, value] of Object.entries(this.tagLog || {})) {
        if (!merged[key] && value?.baseline) {
          merged[key] = { ...buildEmptyTagEntry(), baseline: true };
        }
      }
      this.tagLog = merged;
    },

    navigateSelection(delta) {
      const filtered = this.filteredSorted;
      const newIndex = this.selectedIndex + delta;
      if (newIndex >= 0 && newIndex < filtered.length) {
        this.selectedIndex = newIndex;
      } else if (newIndex < 0 && filtered.length > 0) {
        this.selectedIndex = 0;
      } else if (newIndex >= filtered.length && filtered.length > 0) {
        this.selectedIndex = filtered.length - 1;
      }
    },

    navigate(offset) {
      const filtered = this.filteredSorted;
      const nextIndex = this.currentIndex + offset;
      if (nextIndex >= 0 && nextIndex < filtered.length) {
        const row = filtered[nextIndex];
        this.openViewer(row, this.viewerMode, nextIndex);
      }
    },

    selectRow(index) {
      this.selectedIndex = index;
    },

    setCursorPosition(bounds, evt) {
      if (!bounds || !evt) return;
      this.cursorX = Math.min(
        100,
        Math.max(0, ((evt.clientX - bounds.left) / bounds.width) * 100)
      );
      this.cursorY = Math.min(
        100,
        Math.max(0, ((evt.clientY - bounds.top) / bounds.height) * 100)
      );
    },

    resetCursor() {
      this.cursorX = 50;
      this.cursorY = 50;
    },
  },
});
