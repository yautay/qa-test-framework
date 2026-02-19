import { defineStore } from "pinia";
import { summaryFor } from "../lib/format";
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
  if (tags.bug) return TAG_PRIORITY.bug;
  if (tags.aso) return TAG_PRIORITY.aso;
  if (tags.baseline) return TAG_PRIORITY.baseline;
  return 3;
}

function hasRowNote(row, tagLog) {
  const key = getRowTagKey(row);
  const text = tagLog?.[key]?.note?.text;
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
    tagLocked: {},
    tags: {
      bug: false,
      aso: false,
      baseline: false,
      note: null,
      bug_reported: false,
      aso_reported: false,
      note_reported: false,
      bug_reported_at: "",
      aso_reported_at: "",
      note_reported_at: "",
      note_reported_hash: "",
    },

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
        const canSendBug = !!tags.bug && !tags.bug_reported;
        const canSendAso = !!tags.aso && !tags.aso_reported;
        const noteText = tags.note?.text || "";
        const noteUpdated = tags.note?.updatedAt || "";
        const noteReportedAt = tags.note_reported_at || "";
        const noteHasText = typeof noteText === "string" && noteText.trim() !== "";
        let canSendNote = false;
        if (noteHasText) {
          if (!tags.note_reported) {
            canSendNote = true;
          } else if (!noteReportedAt) {
            canSendNote = true;
          } else if (!noteUpdated) {
            canSendNote = true;
          } else {
            const updatedMs = Date.parse(noteUpdated);
            const reportedMs = Date.parse(noteReportedAt);
            if (!Number.isNaN(updatedMs) && !Number.isNaN(reportedMs)) {
              canSendNote = updatedMs > reportedMs;
            } else {
              canSendNote = true;
            }
          }
        }
        return count + (canSendBug || canSendAso || canSendNote ? 1 : 0);
      }, 0);
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

      if (row) {
        const key = getRowTagKey(row);
        this.tags = this.tagLog[key]
          ? { ...this.tagLog[key] }
          : {
              bug: false,
              aso: false,
              baseline: false,
              note: null,
              bug_reported: false,
             aso_reported: false,
              note_reported: false,
              bug_reported_at: "",
             aso_reported_at: "",
              note_reported_at: "",
              note_reported_hash: "",
            };
        this.tagLocked = this.tagLocked || {};
        const existingLock = this.tagLocked[key] || { bug: false, aso: false, baseline: false };
        this.tagLocked[key] = {
          bug: existingLock.bug || !!this.tags.bug || !!this.tags.bug_reported,
          aso: existingLock.aso || !!this.tags.aso || !!this.tags.aso_reported,
          baseline: existingLock.baseline || !!this.tags.baseline,
        };
      }
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

    toggleTag(tagKey) {
      if (!this.modalRow) return;
      this.tags[tagKey] = true;
      const key = getRowTagKey(this.modalRow);
      const existing = this.tagLog[key] || {};
      this.tagLog[key] = { ...existing, ...this.tags };
      this.tagLocked[key] = this.tagLocked[key] || { bug: false, aso: false, baseline: false };
      this.tagLocked[key][tagKey] = true;
    },

    removeTag(tagKey) {
      if (!this.modalRow) return;
      const key = getRowTagKey(this.modalRow);
      if (this.tagLog[key]) {
        this.tagLog[key][tagKey] = false;
      }
      if (this.tags) {
        this.tags[tagKey] = false;
      }
      this.tagLocked = this.tagLocked || {};
      this.tagLocked[key] = this.tagLocked[key] || { bug: false, aso: false, baseline: false };
      this.tagLocked[key][tagKey] = false;
    },

    isTagLocked(type) {
      if (!this.modalRow) return false;
      const key = getRowTagKey(this.modalRow);
      return !!this.tagLocked?.[key]?.[type];
    },

    isTagReported(type) {
      if (!this.modalRow) return false;
      const key = getRowTagKey(this.modalRow);
      const tags = this.tagLog?.[key] || {};
      if (type === "bug") return !!tags.bug_reported;
      if (type === "aso") return !!tags.aso_reported;
      return false;
    },

    updateTagLog(snapshot) {
      if (!snapshot || typeof snapshot !== "object") {
        this.tagLog = {};
        return;
      }
      const normalized = {};
      for (const [key, value] of Object.entries(snapshot)) {
        if (!value || typeof value !== "object") {
          normalized[key] = value;
          continue;
        }
        normalized[key] = {
          bug: !!value.bug,
          aso: !!value.aso,
          baseline: !!value.baseline,
          note: value.note && typeof value.note === "object" ? { ...value.note } : null,
          bug_reported: !!value.bug_reported,
          aso_reported: !!value.aso_reported,
          note_reported: !!value.note_reported,
          bug_reported_at: String(value.bug_reported_at || ""),
          aso_reported_at: String(value.aso_reported_at || ""),
          note_reported_at: String(value.note_reported_at || ""),
          note_reported_hash: String(value.note_reported_hash || ""),
        };
      }
      this.tagLog = normalized;
    },

    setNoteForCurrentRow(note) {
      if (!this.modalRow) return;
      const key = getRowTagKey(this.modalRow);
      const existing = this.tagLog[key];
      if (!existing) {
        this.tagLog[key] = {
          bug: false,
         aso: false,
          baseline: false,
          note: null,
          bug_reported: false,
         aso_reported: false,
          note_reported: false,
          bug_reported_at: "",
         aso_reported_at: "",
          note_reported_at: "",
          note_reported_hash: "",
        };
      }
      if (note) {
        this.tagLog[key].note = { text: note, updatedAt: new Date().toISOString() };
      } else {
        this.tagLog[key].note = null;
        this.tagLog[key].note_reported_at = "";
        this.tagLog[key].note_reported_hash = "";
        this.tagLog[key].note_reported = false;
      }
      this.tags = { ...this.tagLog[key] };
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
