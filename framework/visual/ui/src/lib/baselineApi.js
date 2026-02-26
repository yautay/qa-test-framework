import { parseJsonResponse } from "./api/parseJsonResponse";

export async function requestBaselineChallengeForRun(runId) {
  const id = encodeURIComponent(String(runId || "").trim());
  const response = await fetch(`/api/reports/${id}/baseline/challenge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(payload?.error || "challenge request failed");
  }
  return payload;
}

export async function sendBaselineSelectionForRun(runId, body) {
  const id = encodeURIComponent(String(runId || "").trim());
  const response = await fetch(`/api/reports/${id}/baseline/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(payload?.error || "baseline send failed");
  }
  return payload;
}
