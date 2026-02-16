const MODE_META = {
  ref: { label: "REF", srcKey: "modalRefSrc" },
  test: { label: "TEST", srcKey: "modalTestSrc" },
  diff: { label: "PIXEL_DIFF", srcKey: "modalDiffSrc" },
  lpips: { label: "LPIPS", srcKey: "modalLpipsSrc" },
};
const MODE_ORDER = ["ref", "test", "diff", "lpips"];
const DEFAULT_SLOT_COUNT = 3;

export function createViewerState() {
  return {
    modal: null,
    fitMode: true, // true = fit width, false = 1:1 (legacy – still used for large zooms)
    viewerMode: "test",     // ref|test|diff|lpips|compare
    modalRow: null,

    slider: 50,
    zoom: 1.0,

    modalTitle: "",
    modalSubtitle: "",

    modalImgSrc: "",
    modalRefSrc: "",
    modalTestSrc: "",
    modalDiffSrc: "",
    modalLpipsSrc: "", // u Ciebie LPIPS = heatmap_path

    columns: 1,
    slots: [],

    // do zoom pod kursorem
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
    viewer.modal = new bootstrap.Modal(document.getElementById(modalElementId));
  }
  return viewer.modal;
}

export function openViewer(viewer, row, mode) {
  // reset
  viewer.modalRow = row;

  viewer.slider = 50;
  viewer.zoom = 1.0;
  viewer.panX = 0;
  viewer.panY = 0;
  viewer.isPanning = false;

  viewer.modalTitle = row.scenario_id || "";
  viewer.modalSubtitle = `status=${row.status || ""} mode=${row.compare_mode || ""}`;

  // źródła (najpierw!)
  viewer.modalRefSrc = row.baseline_path || "";
  viewer.modalTestSrc = row.actual_path || "";
  viewer.modalDiffSrc = row.diff_path || "";
  viewer.modalLpipsSrc = row.heatmap_path || ""; // LPIPS = heatmap

  // fallback mode (dopiero teraz, bo mamy już src)
  if (mode === "ref" && !viewer.modalRefSrc) mode = "test";
  if (mode === "diff" && !viewer.modalDiffSrc) mode = "test";
  if (mode === "lpips" && !viewer.modalLpipsSrc) mode = "test";
  if (mode === "compare" && (!viewer.modalRefSrc || !viewer.modalTestSrc)) mode = "test";

  // ustaw finalny tryb
  viewer.viewerMode = mode;

  // wybór obrazu dla trybów single
  if (mode === "ref") viewer.modalImgSrc = viewer.modalRefSrc;
  else if (mode === "test") viewer.modalImgSrc = viewer.modalTestSrc;
  else if (mode === "diff") viewer.modalImgSrc = viewer.modalDiffSrc;
  else if (mode === "lpips") viewer.modalImgSrc = viewer.modalLpipsSrc;
  else viewer.modalImgSrc = ""; // compare

  viewer.slots = buildSlots(viewer);
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

// zoom pod kursorem: wheel event na kontenerze
export function onWheelZoom(viewer, evt) {
  if (!evt.ctrlKey) return;
  evt.preventDefault();

  const delta = evt.deltaY;
  const direction = delta > 0 ? -1 : 1; // wheel up -> zoom in (zależnie od urządzenia)
  const factor = direction > 0 ? 1.1 : 0.9;

  const oldZoom = viewer.zoom;
  const newZoom = Math.min(6, Math.max(0.25, +(oldZoom * factor).toFixed(3)));
  if (newZoom === oldZoom) return;

  // przesuń tak, by punkt pod kursorem “został”
  const rect = evt.currentTarget.getBoundingClientRect();
  const cx = evt.clientX - rect.left;
  const cy = evt.clientY - rect.top;

  // przelicz offsety
  viewer.panX = (viewer.panX - cx) * (newZoom / oldZoom) + cx;
  viewer.panY = (viewer.panY - cy) * (newZoom / oldZoom) + cy;

  viewer.zoom = newZoom;
}

// proste panowanie (drag) – opcjonalne, ale przy zoomie mega przydatne
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

function getModeList(viewer) {
  return MODE_ORDER.map((mode) => {
    const meta = MODE_META[mode];
    return {
      value: mode,
      label: meta.label,
      srcKey: meta.srcKey,
      available: Boolean(viewer[meta.srcKey]),
    };
  });
}

export function getModeSrc(viewer, mode) {
  const meta = MODE_META[mode];
  if (!meta) return "";
  return viewer[meta.srcKey] || "";
}

function getFirstAvailableMode(viewer, fallbackMode) {
  const modes = getModeList(viewer).filter((m) => m.available);
  if (modes.length === 0) return fallbackMode || "";
  return modes[0].value;
}

function buildSlots(viewer) {
  const availableModes = getModeList(viewer).filter((m) => m.available);
  const slotCount = Math.max(DEFAULT_SLOT_COUNT, availableModes.length || 1);
  const fallbackMode = getFirstAvailableMode(viewer, viewer.viewerMode);
  const slots = Array.from({ length: slotCount }, (_, idx) => {
    const mode = availableModes.length
      ? availableModes[idx % availableModes.length].value
      : fallbackMode;
    return { id: idx + 1, mode };
  });
  return slots;
}

export function getAvailableModes(viewer) {
  return getModeList(viewer);
}
