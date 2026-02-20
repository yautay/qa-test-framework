<template>
  <div class="report-wrap">
    <AppHeader />
    <ReportHeader
      :run-id="runId"
      :store="store"
      :pdf-generated="pdfGenerated"
      @send-baseline="sendBaseline"
      @send-report="promptSendReport"
    />

    <div v-if="store.loadError" class="alert alert-danger py-2">{{ store.loadError }}</div>

    <FiltersPanel />
    <ResultsTable 
      :rows="store.filteredSorted" 
      :fmt="fmt" 
      :tag-log="store.tagLog" 
      :tag-key-for-row="getRowTagKey"
      :selected-index="store.selectedIndex"
      @show="show"
      @select="store.selectRow"
      @open-note="openNoteFromTable"
      @open-metadata="openMetadataFromTable"
    />
    <div v-if="store.selectedIndex >= 0" class="keyboard-hint text-muted small mb-2">
      {{ t('navigate.backToHero') }}
    </div>
    <ViewerModal
      :viewer="viewerForModal"
      :grid-style="store.gridStyle"
      :presentation-style="presentationStyle"
      :image-style="imageStyle"
      :prompt="prompt"
      :note-editor="noteEditor"
      :note-max-length="noteMaxLength"
      :key-held="keyHeld"
      :super-zoom-active="superZoomActive"
      :slot-image="slotImage"
      @set-columns="store.setColumns"
      @set-slot-mode="store.setSlotMode"
      @navigate="store.navigate"
      @super-zoom-down="handleSuperZoomPointerDown"
      @super-zoom-up="handleSuperZoomPointerUp"
      @prompt-tag="promptTag"
      @prompt-remove-tag="promptRemoveTag"
      @open-note="openNoteEditor"
      @open-metadata="openMetadataFromModal"
      @note-input="updateNoteDraft"
      @save-note="saveNoteFromEditor"
      @cancel-note="cancelNoteEditor"
      @delete-note="deleteNoteFromEditor"
      @close-modal="closeModal"
      @reset-cursor="store.resetCursor"
      @mouse-move="handleMouseMove"
    />
    <ConfirmPrompt
      :active="prompt.active"
      :type="prompt.type"
      @confirm="confirmPrompt"
      @cancel="cancelPrompt"
    />
    <TestMetadataPanel
      :active="metadataPanel.active"
      :metadata="metadataPanel.payload"
      @close="closeMetadataPanel"
    />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from "vue";
import AppHeader from "../components/AppHeader.vue";
import ReportHeader from "../components/ReportHeader.vue";
import FiltersPanel from "../components/FiltersPanel.vue";
import ResultsTable from "../components/ResultsTable.vue";
import TestMetadataPanel from "../components/TestMetadataPanel.vue";
import ViewerModal from "../components/ViewerModal.vue";
import ConfirmPrompt from "../components/ConfirmPrompt.vue";
import { fmt } from "../lib/format";
import { t } from "../lib/i18n";
import { useResultsStore } from "../stores/resultsStore";
import { Modal } from "bootstrap";
import { getRowTagKey } from "../lib/viewer";
import { loadTagSnapshot, saveTagSnapshotToFile } from "../lib/tagPersistence";
import { requestBaselineChallengeForRun, sendBaselineSelectionForRun } from "../lib/baselineApi";
import { fetchReportResults, sendRunReport, sendSingleAttempt, retryFailedAttempts } from "../lib/api/reportsApi";
import { NOTE_MAX_LENGTH, normalizeNoteDraft, sanitizeNoteText } from "../lib/notes";
import { buildReportAssetSrc, buildRefApiSrc } from "../composables/useUrlUtils";

const props = defineProps({
  runId: {
    type: String,
    default: "",
  },
});

const store = useResultsStore();
const superZoomActive = ref(false);
const keyHeld = ref({ a: false, d: false, w: false, s: false, c: false });
const prompt = ref({ active: false, type: null });
const tagSyncTimer = ref(null);
const pdfGenerated = ref(false);
const isSendingInProgress = ref(false);
const noteEditor = ref({
  active: false,
  rowKey: "",
  text: "",
  hasExisting: false,
});
const metadataPanel = ref({
  active: false,
  payload: {},
});
const noteMaxLength = NOTE_MAX_LENGTH;

const baseZoom = ref(100);

function isDebugEnabled() {
  return document.cookie.split(';').some(c => c.trim().startsWith('debug=1'));
}

function debugLog(...args) {
  if (isDebugEnabled()) {
    console.log("[DEBUG]", new Date().toISOString(), ...args);
  }
}

const viewerForModal = computed(() => ({
  modalOpen: store.modalOpen,
  viewerMode: store.viewerMode,
  modalRow: store.modalRow,
  modalTitle: store.modalTitle,
  modalSubtitle: store.modalSubtitle,
  modalRefSrc: store.modalRow ? buildRefApiSrc(props.runId, store.modalRow) : "",
  modalTestSrc: store.modalRow ? buildReportAssetSrc(props.runId, store.modalRow.actual_path) : "",
  modalDiffSrc: store.modalRow ? buildReportAssetSrc(props.runId, store.modalRow.diff_path) : "",
  modalLpipsSrc: store.modalRow ? buildReportAssetSrc(props.runId, store.modalRow.heatmap_path) : "",
  modalImgSrc: "",
  columns: store.columns,
  cursorX: store.cursorX,
  cursorY: store.cursorY,
  tags: store.currentTags,
  tagLog: store.tagLog,
  currentIndex: store.currentIndex,
  slots: store.slots,
  slotModes: store.slotModes,
  modal: null,
}));

const zoomScale = computed(() => {
  const level = superZoomActive.value ? baseZoom.value + 200 : baseZoom.value;
  return level / 100;
});

const presentationStyle = computed(() => ({
  width: "100%",
  height: "100%",
  objectFit: "contain",
  objectPosition: "center",
}));

const imageStyle = computed(() => ({
  transform: `scale(${zoomScale.value})`,
  transformOrigin: `${store.cursorX}% ${store.cursorY}%`,
}));

function slotImage(slot) {
  const mode = slot?.mode;
  if (mode === "ref") return viewerForModal.value.modalRefSrc;
  if (mode === "test") return viewerForModal.value.modalTestSrc;
  if (mode === "diff") return viewerForModal.value.modalDiffSrc;
  if (mode === "lpips") return viewerForModal.value.modalLpipsSrc;
  return "";
}

async function loadResults() {
  store.loadError = "";
  if (!props.runId) {
    store.setRows([]);
    store.selectedIndex = -1;
    store.loadError = "Missing run id in URL";
    return;
  }
  store.setRunId(props.runId);
  try {
    const rows = await fetchReportResults(props.runId);
    store.setRows(rows);
    if (store.filteredSorted.length > 0) {
      store.selectedIndex = 0;
    } else {
      store.selectedIndex = -1;
    }
  } catch (error) {
    store.setRows([]);
    store.selectedIndex = -1;
    store.loadError = `Unable to load results: ${error?.message || "unknown error"}`;
  }
}

async function loadTags() {
  if (!props.runId) return;
  const snapshot = await loadTagSnapshot(props.runId);
  if (!snapshot || typeof snapshot !== "object") return;
  store.updateTagLog(snapshot);
}

function persistTags() {
  scheduleTagFileSync();
}

function scheduleTagFileSync() {
  if (!props.runId) {
    return;
  }
  if (tagSyncTimer.value) {
    window.clearTimeout(tagSyncTimer.value);
  }
  const runId = props.runId;
  tagSyncTimer.value = window.setTimeout(async () => {
    const synced = await saveTagSnapshotToFile(store.tagLog, runId);
  }, 250);
}

async function sendBaseline() {
  const candidates = store.baselineCandidates;
  if (!candidates.length) {
    console.info("No BASELINE-tagged TEST artifacts selected");
    return;
  }

  let challenge;
  try {
    challenge = await requestBaselineChallengeForRun(props.runId);
  } catch (_error) {
    console.info("SEND BASELINE requires report server (run make visual-report-serve)");
    return;
  }

  const phrase = String(challenge?.phrase || "").trim();
  const challengeId = String(challenge?.challenge_id || "").trim();
  if (!phrase || !challengeId) {
    console.info("Unable to start baseline confirmation challenge");
    return;
  }

  const typed = window.prompt(`Type this phrase to confirm baseline write:\n\n${phrase}`);
  if (typed === null) {
    console.info("SEND BASELINE cancelled");
    return;
  }

  const items = candidates.map((row) => ({
    scenario_id: row.scenario_id || "",
    suite_id: row.suite_id || "",
    viewport: row.viewport || "",
    browser: row.browser || "",
    actual_path: row.actual_path || "",
  }));

  try {
    const response = await sendBaselineSelectionForRun(props.runId, {
      challenge_id: challengeId,
      phrase: String(typed).trim(),
      items,
    });
    const saved = Number(response?.saved_count || 0);
    const failed = Number(response?.failed_count || 0);
    console.info(`Baseline sync done: saved=${saved}, failed=${failed}`);
  } catch (error) {
    console.info(`SEND BASELINE failed: ${error?.message || "unknown error"}`);
  }
}

async function promptSendReport() {
  if (isSendingInProgress.value) {
    debugLog("DEBUG promptSendReport: sending in progress, skipping");
    return;
  }

  if (!props.runId) {
    console.info("Missing run id, unable to send report");
    return;
  }

  isSendingInProgress.value = true;
  debugLog("DEBUG promptSendReport: starting RAPORT flow (retry failed + PDF)");

  try {
    const retryResult = await retryFailedAttempts(props.runId);
    debugLog("DEBUG retryFailedAttempts result:", retryResult);

    if (retryResult?.tag_snapshot && typeof retryResult.tag_snapshot === "object") {
      store.updateTagLog(retryResult.tag_snapshot);
    }

    console.info(`Retry completed: retried=${retryResult?.retried || 0}`);
  } catch (error) {
    debugLog("DEBUG retryFailedAttempts error:", error?.message);
  }

  const hasAnyBug = store.hasAnyBug > 0;
  if (!hasAnyBug) {
    console.info("No BUG for PDF");
    isSendingInProgress.value = false;
    return;
  }

  await executeSendReport();
}

async function executeSendReport() {
  if (!props.runId) return;
  isSendingInProgress.value = true;
  debugLog("DEBUG executeSendReport: starting");
  const payload = {
    tag_snapshot: store.tagLog,
  };
  try {
    const response = await sendRunReport(props.runId, payload);
    debugLog("DEBUG executeSendReport response:", JSON.stringify(response).slice(0, 500));
    debugLog("DEBUG response keys:", Object.keys(response || {}));
    if (response?.tag_snapshot && typeof response.tag_snapshot === "object") {
      store.updateTagLog(response.tag_snapshot);
    }
    const bug = response?.bug || {};
    const aso = response?.aso || {};
    const note = response?.note || {};
    const pdf = response?.pdf || {};
    const pdfInfo = Number(pdf.pages || 0) > 0 ? `, pdf_pages=${Number(pdf.pages || 0)}` : "";
    const hasNote = typeof note === "object" && note !== null && Object.keys(note).length > 0;
    const noteInfo = hasNote
      ? `, note sent=${Number(note.sent || 0)} failed=${Number(note.failed || 0)} skipped=${Number(note.skipped_locked || 0)}`
      : "";
    console.info(`Report sent: bug sent=${Number(bug.sent || 0)} failed=${Number(bug.failed || 0)} skipped=${Number(bug.skipped_locked || 0)}, aso sent=${Number(aso.sent || 0)} failed=${Number(aso.failed || 0)} skipped=${Number(aso.skipped_locked || 0)}${noteInfo}${pdfInfo}`);
    if (Number(pdf.pages || 0) > 0) {
      pdfGenerated.value = true;
      downloadBugPdf();
    }
    persistTags();
  } catch (error) {
    if (error?.isNoResponse || error?.code === "NO_RESPONSE" || error?.name === "AbortError") {
      return;
    }
    console.info(`RAPORT failed: ${error?.message || "unknown error"}`);
  } finally {
    isSendingInProgress.value = false;
    debugLog("DEBUG executeSendReport: finished, isSendingInProgress = false");
  }
}

function downloadBugPdf() {
  if (!props.runId) return;
  const run = String(props.runId || "").trim();
  if (!run) return;
  const href = `/reports/${encodeURIComponent(run)}/${encodeURIComponent(run)}.pdf?ts=${Date.now()}`;
  const a = document.createElement("a");
  a.href = href;
  a.download = `${run}.pdf`;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function show(row, mode, index = null) {
  const fallbackMode = store.viewerMode || "test";
  const normalizedMode = mode === "compare" ? fallbackMode : (mode || fallbackMode);
  store.openViewer(row, normalizedMode, index);
  const modalEl = document.getElementById("vrtModal");
  if (modalEl) {
    const modal = Modal.getOrCreateInstance(modalEl);
    modal.show();
  }
}

function openNoteEditor(row = store.modalRow) {
  if (!row) return;
  if (prompt.value.active) return;
  const key = getRowTagKey(row);
  const note = store.tagLog?.[key]?.note || null;
  noteEditor.value = {
    active: true,
    rowKey: key,
    text: note?.text || "",
    hasExisting: !!(note && note.text),
  };
}

function openNoteFromTable(row, index) {
  if (typeof index === "number") {
    store.selectedIndex = index;
  }
  show(row, "test", index);
  openNoteEditor(row);
}

function buildMetadataPayload(row) {
  const source = row && typeof row === "object" ? row : {};
  const candidate = source.test_metadata;
  const metadata = candidate && typeof candidate === "object" ? { ...candidate } : {};
  const runSection = metadata.run && typeof metadata.run === "object" ? { ...metadata.run } : {};
  runSection.run_id = runSection.run_id || props.runId || "";
  runSection.tester = runSection.tester || source.tester || "";
  runSection.run_note = runSection.run_note || source.run_note || "";
  metadata.run = runSection;

  const resultSection = metadata.result && typeof metadata.result === "object" ? { ...metadata.result } : {};
  resultSection.scenario_id = resultSection.scenario_id || source.scenario_id || "";
  resultSection.status = resultSection.status || source.status || "";
  resultSection.message = resultSection.message || source.message || "";
  resultSection.viewport = resultSection.viewport || source.viewport || "";
  resultSection.browser = resultSection.browser || source.browser || "";
  metadata.result = resultSection;
  return metadata;
}

function openMetadataFromTable(row, index) {
  if (typeof index === "number") {
    store.selectedIndex = index;
  }
  metadataPanel.value = {
    active: true,
    payload: buildMetadataPayload(row),
  };
}

function openMetadataFromModal() {
  metadataPanel.value = {
    active: true,
    payload: buildMetadataPayload(store.modalRow || {}),
  };
}

function closeMetadataPanel() {
  metadataPanel.value = {
    active: false,
    payload: {},
  };
}

function updateNoteDraft(value) {
  if (!noteEditor.value.active) return;
  const safeText = normalizeNoteDraft(value);
  noteEditor.value = {
    ...noteEditor.value,
    text: safeText,
  };
}

function saveNoteFromEditor() {
  const now = Date.now();
  if (now - lastPromptTime < PROMPT_DEBOUNCE_MS) {
    return;
  }
  if (!noteEditor.value.active || !store.modalRow) return;
  if (prompt.value.active) return;

  const key = getRowTagKey(store.modalRow);
  const existingNote = store.tagLog?.[key]?.note;
  const existingText = existingNote?.text || "";
  const newText = noteEditor.value.text;
  const hasChanged = newText !== existingText;

  lastPromptTime = now;
  if (hasChanged || !existingNote?.text) {
    prompt.value = { active: true, type: "save-note" };
  } else {
    cancelNoteEditor();
  }
}

async function confirmSaveNote() {
  if (!noteEditor.value.active || !store.modalRow) return;
  const safeText = sanitizeNoteText(noteEditor.value.text);
  store.setNoteForCurrentRow(safeText ? safeText : null);
  persistTags();
  cancelNoteEditor();
  await sendTagToBackend("note");
}

function deleteNoteFromEditor() {
  if (!noteEditor.value.active || !store.modalRow) return;
  store.setNoteForCurrentRow(null);
  persistTags();
  cancelNoteEditor();
}

function cancelNoteEditor() {
  if (!noteEditor.value.active) return;
  noteEditor.value = {
    active: false,
    rowKey: "",
    text: "",
    hasExisting: false,
  };
}

function openSelectedRow() {
  if (store.selectedIndex >= 0 && store.selectedIndex < store.filteredSorted.length) {
    const row = store.filteredSorted[store.selectedIndex];
    show(row, "test", store.selectedIndex);
  }
}

function goToHero() {
  window.history.pushState({}, "", "/");
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function handleKeydown(evt) {
  const modalEl = document.getElementById("vrtModal");
  const isOpen = modalEl && modalEl.classList.contains("show");

  if (!isOpen) {
    handleKeydownNonModal(evt);
    return;
  }

  if (handlePromptKeydown(evt)) return;

  if (noteEditor.value.active) {
    return;
  }

  const k = evt.key;

  if (["1", "2", "3", "4"].includes(k)) {
    store.setColumns(Number(k));
  } else if (k.toUpperCase() === "A") {
    evt.preventDefault();
    keyHeld.value.a = true;
    store.navigate(-1);
  } else if (k.toUpperCase() === "D") {
    evt.preventDefault();
    keyHeld.value.d = true;
    store.navigate(1);
  } else if (k.toUpperCase() === "W") {
    if (!superZoomActive.value) {
      keyHeld.value.w = true;
      activateSuperZoom();
    }
  } else if (k.toUpperCase() === "S") {
    if (!store.isTagLocked("bug")) {
      promptTag("bug");
    }
  } else if (k.toUpperCase() === "C") {
    if (!store.isTagLocked("aso")) {
      promptTag("aso");
    }
  } else if (k === "\\") {
    if (!store.isTagLocked("baseline")) {
      promptTag("baseline");
    }
  } else if (k.toUpperCase() === "N") {
    openNoteEditor();
  } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
    const modalEl = document.getElementById("vrtModal");
    if (modalEl) {
      const modal = Modal.getOrCreateInstance(modalEl);
      modal.hide();
    }
  } else if (k === "Escape") {
    const modalEl = document.getElementById("vrtModal");
    if (modalEl) {
      const modal = Modal.getInstance(modalEl);
      modal?.hide();
    }
  }
}

function handleKeydownNonModal(evt) {
  if (handlePromptKeydown(evt)) return;

  if (noteEditor.value.active) {
    return;
  }

  const k = evt.key;

  if (evt.code === "ArrowUp") {
    evt.preventDefault();
    store.navigateSelection(-1);
  } else if (evt.code === "ArrowDown") {
    evt.preventDefault();
    store.navigateSelection(1);
  } else if (evt.code === "Space") {
    evt.preventDefault();
    openSelectedRow();
  } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
    goToHero();
  } else if (k === "Escape") {
    store.selectedIndex = -1;
  }
}

function handleKeyup(evt) {
  if (noteEditor.value.active) {
    return;
  }
  const k = evt.key;
  if (k.toUpperCase() === "A") keyHeld.value.a = false;
  if (k.toUpperCase() === "D") keyHeld.value.d = false;
  if (k.toUpperCase() === "W") {
    keyHeld.value.w = false;
    deactivateSuperZoom();
  }
}

function handleSuperZoomPointerDown() {
  if (!superZoomActive.value) {
    keyHeld.value.w = true;
    activateSuperZoom();
  }
}

function handleSuperZoomPointerUp() {
  if (superZoomActive.value) {
    keyHeld.value.w = false;
    deactivateSuperZoom();
  }
}

function activateSuperZoom() {
  superZoomActive.value = true;
}

function deactivateSuperZoom() {
  superZoomActive.value = false;
}

let lastPromptTime = 0;
const PROMPT_DEBOUNCE_MS = 300;

function promptTag(type) {
  const now = Date.now();
  if (now - lastPromptTime < PROMPT_DEBOUNCE_MS) {
    return;
  }
  if (prompt.value.active) return;
  if (noteEditor.value.active) return;
  if (type === "bug" || type === "aso") {
    if (store.isTagReported(type)) return;
  }
  if (store.isTagLocked(type)) return;
  lastPromptTime = now;
  prompt.value = { active: true, type };
}

function handlePromptKeydown(evt) {
  if (!prompt.value.active) return false;
  evt.preventDefault();
  evt.stopPropagation();
  if (evt.code === "Space") {
    confirmPrompt();
    return true;
  }
  if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
    cancelPrompt();
    return true;
  }
  return true;
}

function promptRemoveTag(type) {
  if (prompt.value.active) return;
  if (noteEditor.value.active) return;
  if (store.isTagReported(type)) return;
  prompt.value = { active: true, type: `remove-${type}` };
}

async function sendTagToBackend(type) {
  if (!props.runId || !store.modalRow) return;

  const key = getRowTagKey(store.modalRow);
  const tags = store.tagLog?.[key] || {};

  let noteHash = null;
  if (type === "note" && tags.note?.text) {
    const text = tags.note.text;
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      const char = text.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    noteHash = hash.toString(16);
  }

  try {
    const result = await sendSingleAttempt(props.runId, key, type, noteHash);
    debugLog("DEBUG sendSingleAttempt result:", result);

    if (result?.tag_snapshot && typeof result.tag_snapshot === "object") {
      store.updateTagLog(result.tag_snapshot);
    }

    if (result?.accepted) {
      console.info(`Tag ${type} sent successfully for ${key}`);
    } else {
      console.info(`Tag ${type} failed to send: ${result?.error || "unknown error"}`);
    }
  } catch (error) {
    console.info(`Send ${type} failed: ${error?.message || "unknown error"}`);
  }
}

async function confirmPrompt() {
  if (!prompt.value.active) return;
  if (prompt.value.type === "send-report") {
    prompt.value = { active: false, type: null };
    await executeSendReport();
    return;
  }
  if (prompt.value.type === "save-note") {
    prompt.value = { active: false, type: null };
    await confirmSaveNote();
    return;
  }
  const type = prompt.value.type?.replace("remove-", "");
  if (prompt.value.type.startsWith("remove-")) {
    store.removeTag(type);
    persistTags();
  } else if (type === "bug" || type === "aso" || type === "note") {
    store.toggleTag(type);
    persistTags();
    await sendTagToBackend(type);
  } else {
    store.toggleTag(type);
    persistTags();
  }
  prompt.value = { active: false, type: null };
}

function cancelPrompt() {
  if (!prompt.value.active) return;
  if (prompt.value.type === "save-note") {
    cancelNoteEditor();
  }
  prompt.value = { active: false, type: null };
}

function closeModal() {
  store.closeViewer();
  deactivateSuperZoom();
  cancelPrompt();
  cancelNoteEditor();
  closeMetadataPanel();
}

function handleMouseMove(payload) {
  const bounds = payload?.bounds;
  const evt = payload?.evt;
  if (!bounds || !evt) return;
  store.setCursorPosition(bounds, evt);
}

onMounted(async () => {
  await loadResults();
  await loadTags();
  window.addEventListener("keydown", handleKeydown);
  window.addEventListener("keyup", handleKeyup);
  const modalEl = document.getElementById("vrtModal");
  if (modalEl) {
    Modal.getOrCreateInstance(modalEl);
    modalEl.addEventListener("hidden.bs.modal", closeModal);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeydown);
  window.removeEventListener("keyup", handleKeyup);
  const modalEl = document.getElementById("vrtModal");
  if (modalEl) {
    modalEl.removeEventListener("hidden.bs.modal", closeModal);
  }
  if (tagSyncTimer.value) {
    window.clearTimeout(tagSyncTimer.value);
    tagSyncTimer.value = null;
  }
});
</script>

<style>
.report-wrap {
  max-width: 96%;
  margin: 0 auto;
}
.keyboard-hint {
  padding: 0.5rem;
  background: var(--card-bg);
  border-radius: 0.25rem;
}
</style>
