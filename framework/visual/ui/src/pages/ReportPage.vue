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
      :sync-errors="store.syncErrors"
      :pending-tags="store.pendingTags"
      @show="show"
      @select="store.selectRow"
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
      @open-metadata="openMetadataFromModal"
      @close-modal="closeModal"
      @reset-cursor="store.resetCursor"
      @mouse-move="handleMouseMove"
    />
    <ConfirmPrompt
      :active="prompt.active"
      :type="prompt.type"
      :note="prompt.note"
      :note-max-length="noteMaxLength"
      @confirm="confirmPrompt"
      @cancel="cancelPrompt"
      @note-input="updatePromptNote"
    />
    <TestMetadataPanel
      :active="metadataPanel.active"
      :metadata="metadataPanel.payload"
      @close="closeMetadataPanel"
    />
    <SyncToasts />
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
import SyncToasts from "../components/SyncToasts.vue";
import { fmt } from "../lib/format";
import { t } from "../lib/i18n";
import { useResultsStore } from "../stores/resultsStore";
import { useReportsStore } from "../stores/reportsStore";
import { Modal } from "bootstrap";
import { getRowTagKey } from "../lib/viewer";
import { requestBaselineChallengeForRun, sendBaselineSelectionForRun } from "../lib/baselineApi";
import {
  fetchReportResults,
  fetchBuildTags,
  postBuildEvent,
  acquireBuildLock,
  heartbeatBuildLock,
  releaseBuildLock,
  sendBuildReport,
} from "../lib/api/reportsApi";
import { NOTE_MAX_LENGTH, normalizeNoteDraft, sanitizeNoteText } from "../lib/notes";
import { buildReportAssetSrc, buildRefApiSrc, buildScenarioTargetUrl } from "../composables/useUrlUtils";
import { useSyncAlerts } from "../composables/useSyncAlerts";
import { fetchAppInfo } from "../lib/api/appInfoApi";
import { SYNC_POLL_INTERVAL_MS } from "../config/syncConfig";

const props = defineProps({
  runId: {
    type: String,
    default: "",
  },
});

const store = useResultsStore();
const reportsStore = useReportsStore();
const { showToast } = useSyncAlerts();
const superZoomActive = ref(false);
const keyHeld = ref({ a: false, d: false, w: false, s: false, c: false });
const pressedKeys = ref(new Set());
const prompt = ref({ active: false, type: null, note: "" });
const pdfGenerated = ref(false);
const isSendingInProgress = ref(false);
const lockInfo = ref({ lockId: "", ownerClientId: "", expiresAt: 0 });
const lockHeartbeatTimer = ref(null);
const lockDenied = ref(false);
const metadataPanel = ref({
  active: false,
  payload: {},
});
const noteMaxLength = NOTE_MAX_LENGTH;

const baseZoom = ref(100);
const HEARTBEAT_MS = 15000;

function rowKey(row) {
  if (!row || typeof row !== "object") return "";
  return [
    String(row.scenario_id || ""),
    String(row.viewport || ""),
    String(row.browser || ""),
  ].join("::");
}

function scenarioTargetEndpoint(row) {
  if (!row || typeof row !== "object") return "";
  const metadata = row.test_metadata;
  if (!metadata || typeof metadata !== "object") return "";
  const scenario = metadata.scenario;
  if (!scenario || typeof scenario !== "object") return "";
  return String(scenario.target_url || "").trim();
}

function scenarioTargetUrl(row) {
  if (!row || typeof row !== "object") return "";
  const metadata = row.test_metadata;
  if (!metadata || typeof metadata !== "object") return "";
  const execution = metadata.execution;
  const baseUrl = execution && typeof execution === "object"
    ? String(execution.target_base_url || "").trim()
    : "";
  const endpoint = scenarioTargetEndpoint(row);
  return buildScenarioTargetUrl(baseUrl, endpoint);
}

function resolvePmsPollingConfig(payload) {
  const uiConfig = payload?.ui_config && typeof payload.ui_config === "object" ? payload.ui_config : {};
  const intervalMs = Math.max(100, Number(uiConfig?.pms_poll_interval_ms || SYNC_POLL_INTERVAL_MS));
  const idleMultiplier = Math.max(1, Number(uiConfig?.pms_poll_idle_multiplier || 1));
  return {
    intervalMs,
    idleMultiplier,
  };
}

async function loadPmsPollingConfig() {
  try {
    const payload = await fetchAppInfo();
    return resolvePmsPollingConfig(payload);
  } catch (_error) {
    return {
      intervalMs: SYNC_POLL_INTERVAL_MS,
      idleMultiplier: 1,
    };
  }
}

function getClientId() {
  const key = "app.client_id";
  if (typeof window === "undefined") return "";
  const existing = window.localStorage.getItem(key);
  if (existing) return existing;
  const generated = window.crypto?.randomUUID
    ? window.crypto.randomUUID()
    : `client_${Math.random().toString(16).slice(2)}_${Date.now()}`;
  window.localStorage.setItem(key, generated);
  return generated;
}

function generateEventId() {
  if (typeof window === "undefined") return `event_${Date.now()}`;
  return window.crypto?.randomUUID
    ? window.crypto.randomUUID()
    : `event_${Math.random().toString(16).slice(2)}_${Date.now()}`;
}

const clientId = getClientId();

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
  modalCaseUrl: store.modalRow ? scenarioTargetUrl(store.modalRow) : "",
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
  syncErrors: store.syncErrors,
  pendingTags: store.pendingTags,
  currentTagKey: store.currentTagKey,
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
  const selectedRow =
    store.selectedIndex >= 0 && store.selectedIndex < store.filteredSorted.length
      ? store.filteredSorted[store.selectedIndex]
      : null;
  const selectedKey = rowKey(selectedRow);
  try {
    const rows = await fetchReportResults(props.runId);
    store.setRows(rows);
    if (store.filteredSorted.length === 0) {
      store.selectedIndex = -1;
      return;
    }
    if (!selectedKey) {
      if (store.selectedIndex < 0) {
        store.selectedIndex = 0;
      }
      return;
    }
    const nextIndex = store.filteredSorted.findIndex((row) => rowKey(row) === selectedKey);
    if (nextIndex >= 0) {
      store.selectedIndex = nextIndex;
    }
  } catch (error) {
    store.setRows([]);
    store.selectedIndex = -1;
    store.loadError = `Unable to load results: ${error?.message || "unknown error"}`;
  }
}

function startLockHeartbeat() {
  if (lockHeartbeatTimer.value) {
    window.clearInterval(lockHeartbeatTimer.value);
  }
  lockHeartbeatTimer.value = window.setInterval(async () => {
    if (!props.runId || !lockInfo.value.lockId) return;
    try {
      const result = await heartbeatBuildLock(props.runId, clientId, lockInfo.value.lockId, {
        timeoutMs: 8000,
      });
      if (!result?.accepted) {
        lockDenied.value = true;
        store.loadError = "Build lock expired or owned by another client.";
        stopLockHeartbeat();
        return;
      }
      const lock = result?.lock || {};
      lockInfo.value = {
        lockId: lock.lock_id || lockInfo.value.lockId,
        ownerClientId: lock.owner_client_id || clientId,
        expiresAt: Number(lock.expires_at || 0),
      };
    } catch (error) {
      store.loadError = `Heartbeat failed: ${error?.message || "unknown error"}`;
    }
  }, HEARTBEAT_MS);
}

function stopLockHeartbeat() {
  if (lockHeartbeatTimer.value) {
    window.clearInterval(lockHeartbeatTimer.value);
    lockHeartbeatTimer.value = null;
  }
}

async function ensureLock() {
  if (!props.runId || !clientId) return false;
  if (lockInfo.value.lockId) return true;
  try {
    const result = await acquireBuildLock(props.runId, clientId, { timeoutMs: 8000 });
    if (!result?.accepted) {
      lockDenied.value = true;
      store.loadError = "Build is locked by another client.";
      return false;
    }
    const lock = result?.lock || {};
    lockInfo.value = {
      lockId: lock.lock_id || "",
      ownerClientId: lock.owner_client_id || clientId,
      expiresAt: Number(lock.expires_at || 0),
    };
    startLockHeartbeat();
    return true;
  } catch (error) {
    store.loadError = `Unable to acquire lock: ${error?.message || "unknown error"}`;
    return false;
  }
}

async function releaseLock() {
  if (!props.runId || !lockInfo.value.lockId) return;
  try {
    await releaseBuildLock(props.runId, clientId, lockInfo.value.lockId, { timeoutMs: 5000 });
  } catch (_error) {
    // best-effort
  } finally {
    lockInfo.value = { lockId: "", ownerClientId: "", expiresAt: 0 };
    stopLockHeartbeat();
  }
}

async function loadState() {
  if (!props.runId) return;
  const payload = await fetchBuildTags(props.runId);
  store.applyBuildTags(payload?.tags || {});
}

function applyStateFromResponse(response) {
  const fullTags = response?.tags;
  if (fullTags && typeof fullTags === "object") {
    store.applyBuildTags(fullTags);
    return;
  }
  const snapshot = response?.test_cases;
  if (!snapshot || typeof snapshot !== "object") return;
  store.updateTagLog(snapshot);
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
    console.error("ERROR SEND BASELINE requires report server (run make visual-report-serve)");
    return;
  }

  const phrase = String(challenge?.phrase || "").trim();
  const challengeId = String(challenge?.challenge_id || "").trim();
  if (!phrase || !challengeId) {
    console.error("ERROR Unable to start baseline confirmation challenge");
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
    if (failed > 0) {
      console.error(`ERROR Baseline sync finished with failures: saved=${saved}, failed=${failed}`);
      return;
    }
    for (const row of candidates) {
      const key = getRowTagKey(row);
      store.setBaselineForKey(key, false);
    }
    console.info(`Baseline sync done: saved=${saved}, failed=${failed}`);
  } catch (error) {
    console.error(`ERROR SEND BASELINE failed: ${error?.message || "unknown error"}`);
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
  const lockOk = await ensureLock();
  if (!lockOk) {
    return;
  }

  isSendingInProgress.value = true;
  debugLog("DEBUG promptSendReport: starting RAPORT flow (flush + PDF)");

  try {
    const response = await sendBuildReport(props.runId, { timeoutMs: 30000 });
    debugLog("DEBUG sendBuildReport response:", JSON.stringify(response).slice(0, 500));
    
    const testCases = response?.test_cases || {};
    for (const [caseKey, caseState] of Object.entries(testCases)) {
      if (caseState?.bug?.locked) {
        store.setPendingTag(caseKey, "bug", { clearError: false, setRetryMarker: false });
      }
      if (caseState?.aso?.locked) {
        store.setPendingTag(caseKey, "aso", { clearError: false, setRetryMarker: false });
      }
    }
    
    applyStateFromResponse(response);
    const pdf = response?.pdf || {};
    if (Number(pdf.pages || 0) > 0) {
      pdfGenerated.value = true;
      downloadBugPdf();
    }
  } catch (error) {
    if (error?.isNoResponse || error?.code === "NO_RESPONSE" || error?.name === "AbortError") {
      return;
    }
    console.info(`RAPORT failed: ${error?.message || "unknown error"}`);
  } finally {
    isSendingInProgress.value = false;
    debugLog("DEBUG promptSendReport: finished, isSendingInProgress = false");
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

async function show(row, mode, index = null) {
  const lockOk = await ensureLock();
  if (!lockOk) return;
  const fallbackMode = store.viewerMode || "test";
  const normalizedMode = mode === "compare" ? fallbackMode : (mode || fallbackMode);
  store.openViewer(row, normalizedMode, index);
  const modalEl = document.getElementById("vrtModal");
  if (modalEl) {
    const modal = Modal.getOrCreateInstance(modalEl);
    modal.show();
  }
}

function buildMetadataPayload(row) {
  const source = row && typeof row === "object" ? row : {};
  const candidate = source.test_metadata;
  const metadata = candidate && typeof candidate === "object" ? { ...candidate } : {};
  const executionSection =
    metadata.execution && typeof metadata.execution === "object"
      ? { ...metadata.execution }
      : {};
  metadata.execution = executionSection;
  const resolvedTargetUrl = scenarioTargetUrl(source);
  if (resolvedTargetUrl) {
    executionSection.target_full_url = resolvedTargetUrl;
  }
  const runSection = metadata.run && typeof metadata.run === "object" ? { ...metadata.run } : {};
  runSection.run_id = runSection.run_id || props.runId || "";
  runSection.tester = runSection.tester || source.tester || "";
  runSection.run_note = runSection.run_note || source.run_note || "";
  const referenceHost =
    runSection.reference_host ||
    executionSection.reference_host ||
    (source.reference_host || "");
  if (referenceHost) {
    runSection.reference_host = referenceHost;
    executionSection.reference_host = executionSection.reference_host || referenceHost;
  }
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

function updatePromptNote(value) {
  if (!prompt.value.active) return;
  const safeText = normalizeNoteDraft(value);
  prompt.value = {
    ...prompt.value,
    note: safeText,
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

function registerKeyPress(evt) {
  if (evt.repeat) return false;
  const code = evt.code || evt.key;
  if (pressedKeys.value.has(code)) return false;
  pressedKeys.value.add(code);
  return true;
}

function releaseKeyPress(evt) {
  const code = evt.code || evt.key;
  pressedKeys.value.delete(code);
}

function handleKeydown(evt) {
  const modalEl = document.getElementById("vrtModal");
  const isOpen = modalEl && modalEl.classList.contains("show");

  if (!isOpen) {
    handleKeydownNonModal(evt);
    return;
  }

  if (prompt.value.active) {
    handlePromptKeydown(evt);
    return;
  }

  if (!registerKeyPress(evt)) return;

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
      evt.preventDefault();
      evt.stopPropagation();
      promptTag("bug");
    }
  } else if (k.toUpperCase() === "C") {
    if (!store.isTagLocked("aso")) {
      evt.preventDefault();
      evt.stopPropagation();
      promptTag("aso");
    }
  } else if (k === "\\") {
    evt.preventDefault();
    evt.stopPropagation();
    promptTag("baseline");
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
  if (prompt.value.active) {
    handlePromptKeydown(evt);
    return;
  }

  if (!registerKeyPress(evt)) return;

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
  releaseKeyPress(evt);
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
  if (type !== "baseline" && store.isTagLocked(type)) return;
  lastPromptTime = now;
  if (type === "baseline") {
    const hasBaseline = !!store.currentTags?.baseline;
    prompt.value = { active: true, type: hasBaseline ? "remove-baseline" : "baseline", note: "" };
    return;
  }
  prompt.value = { active: true, type, note: "" };
}

function handlePromptKeydown(evt) {
  if (!prompt.value.active) return false;
  if (prompt.value.type === "bug" || prompt.value.type === "aso") {
    return false;
  }
  const target = evt.target;
  const tagName = target?.tagName?.toLowerCase?.();
  if (tagName === "textarea" || tagName === "input") {
    return false;
  }
  if (!registerKeyPress(evt)) return true;
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
  if (type !== "baseline") return;
  prompt.value = { active: true, type: `remove-${type}`, note: "" };
}

async function postEvent(eventType, payload) {
  if (!props.runId || !store.modalRow) return;
  const lockOk = await ensureLock();
  if (!lockOk) return;
  const key = getRowTagKey(store.modalRow);
  const tagType = eventType === "BUG_SET" ? "bug" : eventType === "ASO_SET" ? "aso" : null;
  
  if (tagType) {
    const existingTag = store.tagLog?.[key];
    if (tagType === 'bug' && existingTag?.bug?.locked) {
      return;
    }
    if (tagType === 'aso' && existingTag?.aso?.locked) {
      return;
    }
    store.setPendingTag(key, tagType);
  }
  
  try {
    const result = await postBuildEvent(props.runId, {
      event_id: generateEventId(),
      type: eventType,
      test_case_id: key,
      payload: payload || {},
    });
    debugLog("DEBUG postBuildEvent result:", result);
    applyStateFromResponse(result);
    if (!result?.accepted) {
      const errorMsg = result?.error || "unknown";
      store.setSyncError(key, errorMsg);
    }
  } catch (error) {
    console.info(`Send ${eventType} failed: ${error?.message || "unknown error"}`);
    const errorMsg = error?.isNoResponse ? "timeout" : error?.message || "unknown";
    store.setSyncError(key, errorMsg);
  }
}

async function sendEventToBackend(type, noteValue) {
  if (type === "bug") {
    const note = sanitizeNoteText(noteValue || "");
    const payload = note ? { note } : {};
    await postEvent("BUG_SET", payload);
    return;
  }
  if (type === "aso") {
    const note = sanitizeNoteText(noteValue || "");
    const payload = note ? { note } : {};
    await postEvent("ASO_SET", payload);
  }
}

async function confirmPrompt() {
  if (!prompt.value.active) return;
  const currentType = prompt.value.type || "";
  const promptNote = prompt.value.note || "";
  prompt.value = { active: false, type: null, note: "" };

  if (currentType.startsWith("remove-")) {
    const type = currentType.replace("remove-", "");
    if (type === "baseline") {
      store.setBaseline(false);
    }
    return;
  }

  if (currentType === "bug" || currentType === "aso") {
    await sendEventToBackend(currentType, promptNote);
    return;
  }

  if (currentType === "baseline") {
    store.toggleBaseline();
  }
}

function cancelPrompt() {
  if (!prompt.value.active) return;
  prompt.value = { active: false, type: null, note: "" };
}

function closeModal() {
  store.closeViewer();
  deactivateSuperZoom();
  cancelPrompt();
  closeMetadataPanel();
}

function handleMouseMove(payload) {
  const bounds = payload?.bounds;
  const evt = payload?.evt;
  if (!bounds || !evt) return;
  store.setCursorPosition(bounds, evt);
}

onMounted(async () => {
  await ensureLock();
  if (!lockDenied.value) {
    const pmsPollingConfig = await loadPmsPollingConfig();
    await loadResults();
    await loadState();
    store.startPolling(props.runId, SYNC_POLL_INTERVAL_MS, {
      pmsPollIntervalMs: pmsPollingConfig.intervalMs,
      pmsPollIdleMultiplier: pmsPollingConfig.idleMultiplier,
    });
  }
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
  store.stopPolling();
  stopLockHeartbeat();
  releaseLock();
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
