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

export function useUrlUtils(runId, row) {
  const modalRefSrc = row ? buildRefApiSrc(runId, row) : "";
  const modalTestSrc = row ? buildReportAssetSrc(runId, row.actual_path) : "";
  const modalDiffSrc = row ? buildReportAssetSrc(runId, row.diff_path) : "";
  const modalLpipsSrc = row ? buildReportAssetSrc(runId, row.heatmap_path) : "";

  function slotImage(slot) {
    const mode = slot?.mode;
    if (mode === "ref") return modalRefSrc;
    if (mode === "test") return modalTestSrc;
    if (mode === "diff") return modalDiffSrc;
    if (mode === "lpips") return modalLpipsSrc;
    return "";
  }

  return {
    modalRefSrc,
    modalTestSrc,
    modalDiffSrc,
    modalLpipsSrc,
    slotImage,
  };
}
