import { parseJsonResponse } from "./parseJsonResponse";

async function postJson(url, body = {}, options = {}) {
  const timeoutMs = typeof options?.timeoutMs === "number" ? options.timeoutMs : 10000;
  const controller = new AbortController();
  const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
      signal: controller.signal,
    });
    const payload = await parseJsonResponse(response);
    if (!response.ok) {
      throw new Error(payload?.error || "unable to submit request");
    }
    return payload && typeof payload === "object" ? payload : {};
  } catch (error) {
    if (error?.name === "AbortError" || error instanceof TypeError) {
      const noResponse = new Error("no response from server");
      noResponse.code = "NO_RESPONSE";
      noResponse.isNoResponse = true;
      throw noResponse;
    }
    throw error;
  } finally {
    globalThis.clearTimeout(timeoutId);
  }
}

export async function fetchReportsList() {
  const response = await fetch("/api/reports", { cache: "no-store" });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(payload?.error || "unable to fetch reports");
  }
  return Array.isArray(payload?.reports) ? payload.reports : [];
}

export async function fetchReportResults(runId) {
  const id = encodeURIComponent(String(runId || "").trim());
  const response = await fetch(`/api/reports/${id}/results`, { cache: "no-store" });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(payload?.error || "unable to fetch report results");
  }
  return Array.isArray(payload?.results) ? payload.results : [];
}

export async function fetchBuildState(runId) {
  const id = encodeURIComponent(String(runId || "").trim());
  const response = await fetch(`/api/builds/${id}/state`, { cache: "no-store" });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(payload?.error || "unable to fetch build state");
  }
  return payload && typeof payload === "object" ? payload : {};
}

export async function postBuildEvent(runId, body = {}, options = {}) {
  const id = encodeURIComponent(String(runId || "").trim());
  return await postJson(`/api/builds/${id}/events`, body, options);
}

export async function acquireBuildLock(runId, clientId, options = {}) {
  const id = encodeURIComponent(String(runId || "").trim());
  return await postJson(`/api/builds/${id}/lock/acquire`, { client_id: clientId }, options);
}

export async function heartbeatBuildLock(runId, clientId, lockId, options = {}) {
  const id = encodeURIComponent(String(runId || "").trim());
  return await postJson(
    `/api/builds/${id}/lock/heartbeat`,
    { client_id: clientId, lock_id: lockId },
    options
  );
}

export async function releaseBuildLock(runId, clientId, lockId, options = {}) {
  const id = encodeURIComponent(String(runId || "").trim());
  return await postJson(
    `/api/builds/${id}/lock/release`,
    { client_id: clientId, lock_id: lockId },
    options
  );
}

export async function sendBuildReport(runId, options = {}) {
  const id = encodeURIComponent(String(runId || "").trim());
  return await postJson(`/api/builds/${id}/report`, {}, options);
}
