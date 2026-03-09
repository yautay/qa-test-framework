export function isAbsoluteUrl(value) {
  const v = String(value || "").trim().toLowerCase();
  return v.startsWith("http://") || v.startsWith("https://") || v.startsWith("data:") || v.startsWith("blob:");
}

export function buildReportAssetSrc(runId, rawPath) {
  const src = String(rawPath || "").trim();
  if (!src) return "";
  if (isAbsoluteUrl(src) || src.startsWith("/")) return src;
  const id = encodeURIComponent(String(runId || "").trim());
  if (!id) return src;
  const trimmed = src.replace(/^\/+/, "");
  return `/reports/${id}/${trimmed}`;
}

export function buildRefApiSrc(runId, row) {
  const id = encodeURIComponent(String(runId || "").trim());
  if (!id || !row) return "";
  const suite = String(row.suite_id || "").trim();
  const scenario = String(row.scenario_id || "").trim();
  const viewport = String(row.viewport || "").trim();
  const browser = String(row.browser || "").trim();
  if (!suite || !scenario || !viewport || !browser) return "";
  const query = new URLSearchParams({
    suite_id: suite,
    scenario_id: scenario,
    viewport,
    browser,
  });
  return `/api/reports/${id}/image/ref?${query.toString()}`;
}

export function buildScenarioTargetUrl(baseUrl, endpoint) {
  const rawEndpoint = String(endpoint || "").trim();
  if (!rawEndpoint) return "";
  if (isAbsoluteUrl(rawEndpoint)) return rawEndpoint;

  const rawBaseUrl = String(baseUrl || "").trim();
  if (!rawBaseUrl) return "";

  try {
    const base = `${rawBaseUrl.replace(/\/+$/, "")}/`;
    return new URL(rawEndpoint, base).toString();
  } catch (_error) {
    return "";
  }
}

