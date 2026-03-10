import { defineStore } from "pinia";
import { summaryFor } from "../lib/format";
import { normalizeCaseStateSnapshot } from "../lib/notes";
import { getRowTagKey } from "../lib/viewer";
import { SYNC_POLL_INTERVAL_MS } from "../config/syncConfig";
import { fetchBuildTags, fetchReportResultsPayload } from "../lib/api/reportsApi";

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
  bug: { locked: false, synced: false, note: "" },
  aso: { locked: false, synced: false, note: "" },
  baseline: false,
};

const PERCEPTUAL_PENDING_STATUSES = new Set(["queued", "running", "pending", "processing", "submitted"]);

function isDebugPollingEnabled() {
  if (typeof document === "undefined") return false;
  return document.cookie.split(";").some((entry) => entry.trim().startsWith("debug=1"));
}

function debugPollingLog(...args) {
  if (!isDebugPollingEnabled()) return;
  console.debug("[POLLING]", ...args);
}

function buildEmptyTagEntry() {
  return {
    bug: { ...EMPTY_TAG_ENTRY.bug },
    aso: { ...EMPTY_TAG_ENTRY.aso },
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
  const bugNote = tagLog?.[key]?.bug?.note || "";
  const asoNote = tagLog?.[key]?.aso?.note || "";
  return [bugNote, asoNote].some((text) => typeof text === "string" && !!text.trim());
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

function tagTypeFromEventType(eventType) {
  const normalized = String(eventType || "").toUpperCase();
  if (normalized === "BUG_SET") return "bug";
  if (normalized === "ASO_SET") return "aso";
  return null;
}

function getPerceptualPayload(row) {
  if (row?.perceptual && typeof row.perceptual === "object") {
    return row.perceptual;
  }
  const nested = row?.test_metadata?.perceptual;
  return nested && typeof nested === "object" ? nested : null;
}

function isPerceptualMode(compareMode) {
  const mode = String(compareMode || "").toLowerCase();
  return mode === "hybrid";
}

function shouldTrackPerceptualRow(row) {
  const payload = getPerceptualPayload(row);
  if (!payload || typeof payload !== "object") {
    return isPerceptualMode(row?.compare_mode);
  }
  const status = String(payload?.status || "").trim().toLowerCase();
  if (PERCEPTUAL_PENDING_STATUSES.has(status)) return true;
  return isPerceptualMode(row?.compare_mode);
}

function getPerceptualPollingStats(rows) {
  if (!Array.isArray(rows) || !rows.length) {
    return {
      hasPendingJobs: false,
      pendingJobs: 0,
      perceptualRows: 0,
      rowsCount: 0,
    };
  }
  let pendingJobs = 0;
  let perceptualRows = 0;
  for (const row of rows) {
    if (!shouldTrackPerceptualRow(row)) continue;
    perceptualRows += 1;
    const payload = getPerceptualPayload(row);
    const status = String(payload?.status || "").trim().toLowerCase();
    if (PERCEPTUAL_PENDING_STATUSES.has(status)) {
      pendingJobs += 1;
    }
  }
  return {
    hasPendingJobs: pendingJobs > 0,
    pendingJobs,
    perceptualRows,
    rowsCount: rows.length,
  };
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
    buildMetadata: {},
    excludedVisualCases: [],

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
    pendingTags: {},
    syncErrors: {},
    retryMarkers: {},
    pollingActive: false,
    pollingIntervalId: null,
    resultsPollingActive: false,
    resultsPollTimeoutId: null,
    resultsPollIntervalMs: SYNC_POLL_INTERVAL_MS,
    pmsPollIdleMultiplier: 1,
    resultsPollMode: "active",

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

        return count + (canSendBug || canSendAso ? 1 : 0);
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
    setRows(rows, options = {}) {
      const reconcileSelection = options?.reconcileSelection !== false;
      const previouslySelectedRow =
        this.selectedIndex >= 0 && this.selectedIndex < this.filteredSorted.length
          ? this.filteredSorted[this.selectedIndex]
          : null;
      const previousSelectedKey = previouslySelectedRow ? getRowTagKey(previouslySelectedRow) : "";
      const previousModalKey = this.modalRow ? getRowTagKey(this.modalRow) : "";

      const normalized = Array.isArray(rows)
        ? rows.map((row) => {
            if (!row || typeof row !== "object") return row;
            const status = row.status === "new" ? "failed" : row.status;
            return { ...row, status };
          })
        : [];

      this.rows = normalized;
      this.summary = summaryFor(normalized);

      if (!reconcileSelection) {
        return;
      }

      if (previousModalKey) {
        const nextModalRow = this.rows.find((row) => getRowTagKey(row) === previousModalKey) || null;
        this.modalRow = nextModalRow;
        if (!nextModalRow) {
          this.modalOpen = false;
          this.currentIndex = null;
        }
      }

      if (previousSelectedKey) {
        const nextSelectedIndex = this.filteredSorted.findIndex((row) => getRowTagKey(row) === previousSelectedKey);
        this.selectedIndex = nextSelectedIndex;
      }

      if (this.currentIndex != null && this.currentIndex >= 0) {
        if (this.modalRow) {
          const nextCurrentIndex = this.filteredSorted.findIndex((row) => getRowTagKey(row) === getRowTagKey(this.modalRow));
          this.currentIndex = nextCurrentIndex >= 0 ? nextCurrentIndex : null;
        } else {
          this.currentIndex = null;
        }
      }
    },

    setBuildMetadata(metadata) {
      const normalized = metadata && typeof metadata === "object" ? { ...metadata } : {};
      this.buildMetadata = normalized;
      const visual = normalized.visual && typeof normalized.visual === "object" ? normalized.visual : {};
      const excluded = Array.isArray(visual.excluded_cases) ? visual.excluded_cases : [];
      this.excludedVisualCases = excluded
        .map((entry) => {
          if (!entry || typeof entry !== "object") return null;
          return {
            nodeid: String(entry.nodeid || ""),
            status: String(entry.status || ""),
            phase: String(entry.phase || ""),
            reason: String(entry.reason || ""),
          };
        })
        .filter((entry) => entry && entry.nodeid);
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

    setBaselineForKey(caseKey, value) {
      if (!caseKey) return;
      const existing = this.tagLog[caseKey] ? { ...this.tagLog[caseKey] } : buildEmptyTagEntry();
      existing.baseline = !!value;
      this.tagLog[caseKey] = existing;
    },

    isTagLocked(type) {
      const tags = this.currentTags;
      if (type === "bug") return !!tags.bug?.locked;
      if (type === "aso") return !!tags.aso?.locked;
      if (type === "baseline") return false;
      return false;
    },

    isTagReported(type) {
      if (!this.modalRow) return false;
      const tags = this.currentTags || {};
      if (type === "bug") return !!tags.bug?.synced;
      if (type === "aso") return !!tags.aso?.synced;
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

    setPendingTag(caseKey, type, options = {}) {
      if (!caseKey || !type) return;
      const clearError = options?.clearError !== false;
      const setRetryMarker = options?.setRetryMarker !== false;
      const existing = this.pendingTags[caseKey] || {};
      this.pendingTags[caseKey] = { ...existing, [type]: true };
      if (clearError) {
        delete this.syncErrors[caseKey];
      }
      if (setRetryMarker) {
        const existingMarkers = this.retryMarkers[caseKey] || {};
        this.retryMarkers[caseKey] = { ...existingMarkers, [type]: Date.now() };
      }
    },

    setOptimisticTag(caseKey, type, noteContent = null) {
      if (!caseKey || !type) return;
      const existing = this.pendingTags[caseKey] || {};
      
      this.pendingTags[caseKey] = { ...existing, [type]: true };
      delete this.syncErrors[caseKey];
      const existingMarkers = this.retryMarkers[caseKey] || {};
      this.retryMarkers[caseKey] = { ...existingMarkers, [type]: Date.now() };
       
      const currentLog = this.tagLog[caseKey] || buildEmptyTagEntry();
      if (type === "bug") {
        currentLog.bug = { ...currentLog.bug, locked: true, synced: false };
      } else if (type === "aso") {
        currentLog.aso = { ...currentLog.aso, locked: true, synced: false };
      }
      this.tagLog[caseKey] = currentLog;
    },

    confirmTagSync(caseKey, type) {
      if (!caseKey || !type) return;
      const pending = this.pendingTags[caseKey];
      if (pending) {
        delete pending[type];
        if (Object.keys(pending).length === 0) {
          delete this.pendingTags[caseKey];
        } else {
          this.pendingTags[caseKey] = pending;
        }
      }
      delete this.syncErrors[caseKey];
      const marker = this.retryMarkers[caseKey];
      if (marker) {
        delete marker[type];
        if (Object.keys(marker).length === 0) {
          delete this.retryMarkers[caseKey];
        } else {
          this.retryMarkers[caseKey] = marker;
        }
      }
    },

    setSyncError(caseKey, message) {
      if (!caseKey) return;
      this.syncErrors[caseKey] = {
        message: message || 'unknown',
        timestamp: Date.now(),
      };
      delete this.pendingTags[caseKey];
      delete this.retryMarkers[caseKey];
    },

    clearSyncError(caseKey) {
      if (!caseKey) return;
      delete this.syncErrors[caseKey];
    },

    hasPendingTag(caseKey, type) {
      return !!this.pendingTags[caseKey]?.[type];
    },

    getSyncError(caseKey) {
      return this.syncErrors[caseKey] || null;
    },

    isPendingTag(caseKey, type) {
      return !!this.pendingTags[caseKey]?.[type];
    },

    startPolling(runId, intervalMs = SYNC_POLL_INTERVAL_MS, options = {}) {
      if (this.pollingActive) return;
      if (!runId) return;
      
      this.pollingActive = true;
      this.runId = runId;
      this.resultsPollIntervalMs = Math.max(100, Number(options?.pmsPollIntervalMs || intervalMs || SYNC_POLL_INTERVAL_MS));
      this.pmsPollIdleMultiplier = Math.max(1, Number(options?.pmsPollIdleMultiplier || 1));
      this.resultsPollMode = "active";

      debugPollingLog(
        `results polling started run_id=${this.runId} base_ms=${this.resultsPollIntervalMs} idle_multiplier=${this.pmsPollIdleMultiplier}`,
      );
      
      this.pollSyncState();
      this.startResultsPolling();
      
      this.pollingIntervalId = setInterval(() => {
        this.pollSyncState();
      }, intervalMs);
    },

    stopPolling() {
      if (this.pollingIntervalId) {
        clearInterval(this.pollingIntervalId);
        this.pollingIntervalId = null;
      }
      this.stopResultsPolling();
      this.pollingActive = false;
      debugPollingLog(`results polling stopped run_id=${this.runId}`);
    },

    startResultsPolling() {
      if (this.resultsPollingActive) return;
      this.resultsPollingActive = true;
      this.scheduleNextResultsPoll(this.resultsPollIntervalMs);
    },

    stopResultsPolling() {
      if (this.resultsPollTimeoutId) {
        clearTimeout(this.resultsPollTimeoutId);
        this.resultsPollTimeoutId = null;
      }
      this.resultsPollingActive = false;
    },

    scheduleNextResultsPoll(delayMs) {
      if (!this.resultsPollingActive) return;
      if (this.resultsPollTimeoutId) {
        clearTimeout(this.resultsPollTimeoutId);
      }
      this.resultsPollTimeoutId = setTimeout(async () => {
        const pollStats = await this.pollResultsState();
        const hasPendingJobs = !!pollStats.hasPendingJobs;
        const base = Math.max(100, Number(this.resultsPollIntervalMs || SYNC_POLL_INTERVAL_MS));
        const multiplier = Math.max(1, Number(this.pmsPollIdleMultiplier || 1));
        const nextMode = hasPendingJobs ? "active" : "idle";
        const nextDelay = hasPendingJobs ? base : Math.round(base * multiplier);
        debugPollingLog("results polling tick", {
          runId: this.runId,
          mode: nextMode,
          previousMode: this.resultsPollMode,
          hasPendingJobs,
          pendingJobs: pollStats.pendingJobs,
          perceptualRows: pollStats.perceptualRows,
          rowsCount: pollStats.rowsCount,
          baseMs: base,
          idleMultiplier: multiplier,
          nextMs: nextDelay,
        });
        if (this.resultsPollMode !== nextMode) {
          this.resultsPollMode = nextMode;
          debugPollingLog(`results polling mode=${nextMode} next_ms=${nextDelay} run_id=${this.runId}`);
        }
        this.scheduleNextResultsPoll(nextDelay);
      }, Math.max(100, Number(delayMs || this.resultsPollIntervalMs || SYNC_POLL_INTERVAL_MS)));
    },

    async pollResultsState() {
      if (!this.runId) {
        return {
          hasPendingJobs: false,
          pendingJobs: 0,
          perceptualRows: 0,
          rowsCount: 0,
        };
      }
      try {
        const payload = await fetchReportResultsPayload(this.runId);
        this.setRows(payload.results, { reconcileSelection: true });
        this.setBuildMetadata(payload.build_metadata);
        return getPerceptualPollingStats(this.rows);
      } catch (_error) {
        return {
          hasPendingJobs: false,
          pendingJobs: 0,
          perceptualRows: 0,
          rowsCount: 0,
        };
      }
    },

    async pollSyncState() {
      if (!this.runId) return;
      
      try {
        const serverTags = await fetchBuildTags(this.runId);
        this.applyBuildTags(serverTags?.tags || {});
      } catch (e) {
        // Silent fail - polling should be resilient
      }
    },

    applyBuildTags(serverTags) {
      if (!serverTags || typeof serverTags !== "object") {
        this.pendingTags = {};
        this.syncErrors = {};
        this.updateTagLog({});
        return;
      }
      const testCases = serverTags?.test_cases || {};
      const outboxEntries = Array.isArray(serverTags?.outbox) ? serverTags.outbox : [];
      this.updateTagLog(testCases);
      this.updateSyncIndicatorsFromOutbox(outboxEntries);
    },

    updateSyncIndicatorsFromOutbox(outboxEntries) {
      const nextPending = {};
      const nextErrors = {};
      const nextMarkers = {};
      const currentMarkers = this.retryMarkers || {};
      const handled = new Set();

      const pendingKey = (caseKey, tagType) => `${caseKey}::${tagType}`;

      const ensurePending = (caseKey, tagType, markerValue) => {
        const pendingEntry = nextPending[caseKey] || {};
        pendingEntry[tagType] = true;
        nextPending[caseKey] = pendingEntry;
        if (!nextMarkers[caseKey]) nextMarkers[caseKey] = {};
        nextMarkers[caseKey][tagType] = markerValue || nextMarkers[caseKey][tagType] || Date.now();
      };

      for (const entry of outboxEntries) {
        if (!entry || typeof entry !== "object") continue;
        const caseKey = String(entry.test_case_id || "").trim();
        const tagType = tagTypeFromEventType(entry.type);
        if (!caseKey || !tagType) continue;
        const status = String(entry.status || "pending").toLowerCase();
        const lastAttempt = Date.parse(entry.last_attempt_at || "") || 0;
        const marker = currentMarkers?.[caseKey]?.[tagType] || 0;
        const key = pendingKey(caseKey, tagType);

        if (status === "pending") {
          const markerValue = marker || Date.now();
          ensurePending(caseKey, tagType, markerValue);
          handled.add(key);
          continue;
        }

        if (status === "failed") {
          if (marker && lastAttempt < marker) {
            ensurePending(caseKey, tagType, marker);
            handled.add(key);
            continue;
          }
          const message = String(entry.last_error || "sync failed").trim() || "sync failed";
          const timestamp = lastAttempt || Date.now();
          nextErrors[caseKey] = { message, timestamp };
          handled.add(key);
          continue;
        }

        // status sent/superseded => success, ensure marker cleared
        handled.add(key);
      }

      for (const [caseKey, tags] of Object.entries(currentMarkers)) {
        for (const [tagType, markerValue] of Object.entries(tags)) {
          const key = pendingKey(caseKey, tagType);
          if (handled.has(key)) {
            continue;
          }
          ensurePending(caseKey, tagType, markerValue);
        }
      }

      this.pendingTags = nextPending;
      this.syncErrors = nextErrors;
      this.retryMarkers = nextMarkers;
    },
  },
});
