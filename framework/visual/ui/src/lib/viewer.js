import { Modal } from "bootstrap";

const MODE_META = {
  ref: { label: "REF", srcKey: "modalRefSrc" },
  test: { label: "TEST", srcKey: "modalTestSrc" },
  diff: { label: "PIXEL_DIFF", srcKey: "modalDiffSrc" },
  lpips: { label: "LPIPS", srcKey: "modalLpipsSrc" },
};
const DEFAULT_SLOT_COUNT = 3;
const DEFAULT_ZOOM = 160;
const SLOT_MODE_DEFAULTS = {
  1: "ref",
  2: "test",
  3: "diff",
  4: "lpips",
};

export function createViewerState() {
  return {
    modal: null,
    fitMode: true,
    viewerMode: "test",
    modalRow: null,

    slider: 50,
    zoom: 1.0,

    modalTitle: "",
    modalSubtitle: "",

    modalImgSrc: "",
    modalRefSrc: "",
    modalTestSrc: "",
    modalDiffSrc: "",
    modalLpipsSrc: "",

    columns: DEFAULT_SLOT_COUNT,
    zoomPreset: DEFAULT_ZOOM,
    cursorX: 50,
    cursorY: 50,
    tags: { bug: false, aso: false },
    tagLog: {},
    tagLocked: {},
    currentIndex: null,
    slots: [],
    slotModes: { 1: "ref", 2: "test", 3: "diff", 4: "lpips" },

    panX: 0,
    panY: 0,
    isPanning: false,
    panStartX: 0,
    panStartY: 0,
  };
}
export function toggleFit(viewer) {
  viewer.fitMode = !viewer.fitMode;
  viewer.zoom = 1.0;
  viewer.panX = 0;
  viewer.panY = 0;
}

export function ensureModal(viewer, modalElementId = "vrtModal") {
  if (!viewer.modal) {
    viewer.modal = new Modal(document.getElementById(modalElementId));
  }
  return viewer.modal;
}

export function openViewer(viewer, row, mode, index = null) {
  viewer.modalRow = row;

  viewer.slider = 50;
  viewer.zoom = 1.0;
  viewer.panX = 0;
  viewer.panY = 0;
  viewer.isPanning = false;

  viewer.modalTitle = row.scenario_id || "";
  viewer.modalSubtitle = `status=${row.status || ""} mode=${row.compare_mode || ""}`;

  viewer.modalRefSrc = row.baseline_path || "";
  viewer.modalTestSrc = row.actual_path || "";
  viewer.modalDiffSrc = row.diff_path || "";
  viewer.modalLpipsSrc = row.heatmap_path || "";

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
    viewer.tags = viewer.tagLog[key] ? { ...viewer.tagLog[key] } : { bug: false, aso: false };
    viewer.tagLocked = viewer.tagLocked || {};
    const existingLock = viewer.tagLocked[key] || { bug: false, aso: false };
    viewer.tagLocked[key] = {
      bug: existingLock.bug || !!viewer.tags.bug,
      aso: existingLock.aso || !!viewer.tags.aso,
    };
  }
}

export function setMode(viewer, mode) {
  if (!viewer.modalRow) return;
  openViewer(viewer, viewer.modalRow, mode);
}

export function zoomIn(viewer) {
  viewer.zoom = Math.min(6, +(viewer.zoom + 0.25).toFixed(2));
}
export function zoomOut(viewer) {
  viewer.zoom = Math.max(0.25, +(viewer.zoom - 0.25).toFixed(2));
}
export function resetZoom(viewer) {
  viewer.zoom = 1.0;
  viewer.panX = 0;
  viewer.panY = 0;
}

export function onWheelZoom(viewer, evt) {
  if (!evt.ctrlKey) return;
  evt.preventDefault();

  const delta = evt.deltaY;
  const direction = delta > 0 ? -1 : 1;
  const factor = direction > 0 ? 1.1 : 0.9;

  const oldZoom = viewer.zoom;
  const newZoom = Math.min(6, Math.max(0.25, +(oldZoom * factor).toFixed(3)));
  if (newZoom === oldZoom) return;

  const rect = evt.currentTarget.getBoundingClientRect();
  const cx = evt.clientX - rect.left;
  const cy = evt.clientY - rect.top;

  viewer.panX = (viewer.panX - cx) * (newZoom / oldZoom) + cx;
  viewer.panY = (viewer.panY - cy) * (newZoom / oldZoom) + cy;

  viewer.zoom = newZoom;
}

export function panStart(viewer, evt) {
  if (evt.button !== 0) return;
  evt.preventDefault();
  viewer.isPanning = true;
  viewer.panStartX = evt.clientX - viewer.panX;
  viewer.panStartY = evt.clientY - viewer.panY;
}
export function panMove(viewer, evt) {
  if (!viewer.isPanning) return;
  viewer.panX = evt.clientX - viewer.panStartX;
  viewer.panY = evt.clientY - viewer.panStartY;
}
export function panEnd(viewer) {
  viewer.isPanning = false;
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
  return `${row.scenario_id || ""}-${row.message || ""}`;
}

export function toggleTag(viewer, row, tagKey) {
  if (!row) return;
  viewer.tags[tagKey] = true;
  const key = getRowTagKey(row);
  viewer.tagLog[key] = { ...viewer.tags };
  viewer.tagLocked[key] = viewer.tagLocked[key] || { bug: false, aso: false };
  viewer.tagLocked[key][tagKey] = true;
}
