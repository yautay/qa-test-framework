import { Modal } from "bootstrap";
import { buildReportAssetSrc, buildRefApiSrc } from "../composables/useUrlUtils";

const MODE_META = {
  ref: { srcKey: "modalRefSrc" },
  test: { srcKey: "modalTestSrc" },
  diff: { srcKey: "modalDiffSrc" },
  lpips: { srcKey: "modalLpipsSrc" },
};
const DEFAULT_SLOT_COUNT = 2;
const SLOT_MODE_DEFAULTS = {
  1: "ref",
  2: "test",
  3: "diff",
  4: "lpips",
};

export function createViewerState() {
  return {
    runId: "",
    modal: null,
    viewerMode: "test",
    modalRow: null,

    modalTitle: "",
    modalSubtitle: "",

    modalImgSrc: "",
    modalRefSrc: "",
    modalTestSrc: "",
    modalDiffSrc: "",
    modalLpipsSrc: "",

    columns: DEFAULT_SLOT_COUNT,
    cursorX: 50,
    cursorY: 50,
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
    tagLog: {},
    tagLocked: {},
    currentIndex: null,
    slots: [],
    slotModes: { 1: "ref", 2: "test", 3: "diff", 4: "lpips" },
  };
}

export function ensureModal(viewer, modalElementId = "vrtModal") {
  if (!viewer.modal) {
    viewer.modal = new Modal(document.getElementById(modalElementId));
  }
  return viewer.modal;
}

export function openViewer(viewer, row, mode, index = null, options = {}) {
  const runId = String(options.runId || viewer.runId || "").trim();
  viewer.runId = runId;
  viewer.modalRow = row;

  viewer.modalTitle = row.scenario_id || "";
  viewer.modalSubtitle = `status=${row.status || ""} mode=${row.compare_mode || ""}`;

  viewer.modalRefSrc = buildRefApiSrc(runId, row);
  viewer.modalTestSrc = buildReportAssetSrc(runId, row.actual_path || "");
  viewer.modalDiffSrc = buildReportAssetSrc(runId, row.diff_path || "");
  viewer.modalLpipsSrc = buildReportAssetSrc(runId, row.heatmap_path || "");

  if (mode === "ref" && !viewer.modalRefSrc) mode = "test";
  if (mode === "diff" && !viewer.modalDiffSrc) mode = "test";
  if (mode === "lpips" && !viewer.modalLpipsSrc) mode = "test";
  if (mode === "compare" && (!viewer.modalRefSrc || !viewer.modalTestSrc)) mode = "test";

  viewer.viewerMode = mode;

  if (mode === "ref") viewer.modalImgSrc = viewer.modalRefSrc;
  else if (mode === "test") viewer.modalImgSrc = viewer.modalTestSrc;
  else if (mode === "diff") viewer.modalImgSrc = viewer.modalDiffSrc;
  else if (mode === "lpips") viewer.modalImgSrc = viewer.modalLpipsSrc;
  else viewer.modalImgSrc = "";

  refreshSlots(viewer);
  viewer.currentIndex = index;
  if (row) {
    const key = getRowTagKey(row);
    viewer.tags = viewer.tagLog[key]
      ? { ...viewer.tagLog[key] }
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
    viewer.tagLocked = viewer.tagLocked || {};
    const existingLock = viewer.tagLocked[key] || { bug: false, aso: false, baseline: false };
    viewer.tagLocked[key] = {
      bug: existingLock.bug || !!viewer.tags.bug || !!viewer.tags.bug_reported,
      aso: existingLock.aso || !!viewer.tags.aso || !!viewer.tags.aso_reported,
      baseline: existingLock.baseline || !!viewer.tags.baseline,
    };
  }
}

export function getModeSrc(viewer, mode) {
  const meta = MODE_META[mode];
  if (!meta) return "";
  return viewer[meta.srcKey] || "";
}

function defaultSlotMode(slotId) {
  return SLOT_MODE_DEFAULTS[slotId] || "test";
}

function buildSlots(viewer, slotCount = viewer.columns || DEFAULT_SLOT_COUNT) {
  const count = Math.max(1, slotCount);
  const existing = new Map((viewer.slots || []).map((slot) => [slot.id, slot]));
  const slotModes = viewer.slotModes || {};
  return Array.from({ length: count }, (_, idx) => {
    const id = idx + 1;
    const previous = existing.get(id);
    const mode = slotModes[id] || previous?.mode || defaultSlotMode(id);
    slotModes[id] = mode;
    return {
      id,
      mode,
    };
  });
}

export function refreshSlots(viewer, slotCount) {
  viewer.slots = buildSlots(viewer, slotCount);
}

export function navigateRow(viewer, rows, offset) {
  if (!Array.isArray(rows) || rows.length === 0) return null;
  if (viewer.currentIndex === null) return null;
  const nextIndex = viewer.currentIndex + offset;
  if (nextIndex < 0 || nextIndex >= rows.length) return null;
  return { row: rows[nextIndex], index: nextIndex };
}

export function setCursorPosition(viewer, bounds, evt) {
  if (!bounds || !evt) return;
  viewer.cursorX = Math.min(100, Math.max(0, ((evt.clientX - bounds.left) / bounds.width) * 100));
  viewer.cursorY = Math.min(100, Math.max(0, ((evt.clientY - bounds.top) / bounds.height) * 100));
}

export function getRowTagKey(row) {
  return [
    row?.scenario_id || "",
    row?.actual_path || "",
    row?.baseline_path || "",
    row?.diff_path || "",
  ].join("::");
}

export function toggleTag(viewer, row, tagKey) {
  if (!row) return;
  viewer.tags[tagKey] = true;
  const key = getRowTagKey(row);
  const existing = viewer.tagLog[key] || {};
  viewer.tagLog[key] = { ...existing, ...viewer.tags };
  viewer.tagLocked[key] = viewer.tagLocked[key] || { bug: false, aso: false, baseline: false };
  viewer.tagLocked[key][tagKey] = true;
}
