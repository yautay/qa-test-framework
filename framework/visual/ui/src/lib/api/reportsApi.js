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
