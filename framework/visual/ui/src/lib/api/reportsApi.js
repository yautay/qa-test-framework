import { parseJsonResponse } from "./parseJsonResponse";

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

export async function sendRunReport(runId, body = {}, options = {}) {
  const id = encodeURIComponent(String(runId || "").trim());
  const timeoutMs = typeof options?.timeoutMs === "number" ? options.timeoutMs : 10000;
  const controller = new AbortController();
  const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`/api/reports/${id}/report/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
      signal: controller.signal,
    });
    const payload = await parseJsonResponse(response);
    if (!response.ok) {
      throw new Error(payload?.error || "unable to send report");
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
