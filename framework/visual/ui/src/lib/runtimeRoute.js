function normalizePath(pathname) {
  const value = String(pathname || "/").trim();
  return value || "/";
}

export function parseRuntimeRoute(pathname) {
  const path = normalizePath(pathname);
  if (path === "/" || path === "/index.html") {
    return { page: "hero", runId: "" };
  }

  const reportMatch = path.match(/^\/reports\/([^/]+)(?:\/index\.html)?\/?$/);
  if (reportMatch) {
    return {
      page: "report",
      runId: decodeURIComponent(reportMatch[1] || ""),
    };
  }

  return { page: "hero", runId: "" };
}

export function reportPath(runId) {
  const id = encodeURIComponent(String(runId || "").trim());
  return id ? `/reports/${id}` : "/";
}
