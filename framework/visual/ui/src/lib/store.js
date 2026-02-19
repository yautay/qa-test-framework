import { summaryFor } from "./format";
import { getRowTagKey } from "./viewer";

const NUMERIC_SORT_KEYS = ["pixel_changed_ratio", "lpips", "dists"];

const STATUS_PRIORITY = {
  failed: 0,
  skipped: 1,
  passed: 2,
};

const TAG_PRIORITY = {
  bug: 0,
  aso: 1,
  baseline: 2,
};

export function createStore() {
  const rows = [];
  return {
    rows,
    q: "",
    status: "",
    viewport: "",
    browser: "",
    sortKey: "scenario_id",
    summary: summaryFor(rows),
  };
}

export function setRows(store, rows) {
  const normalized = Array.isArray(rows)
    ? rows.map((row) => {
      if (!row || typeof row !== "object") return row;
      const status = row.status === "error" || row.status === "new" ? "failed" : row.status;
      return { ...row, status };
    })
    : [];
  store.rows = normalized;
  store.summary = summaryFor(normalized);
}

function compareValues(av, bv, key) {
  if (av == null && bv == null) return 0;
  if (av == null) return 1;
  if (bv == null) return -1;

  if (key === "status") {
    const aPriority = STATUS_PRIORITY[av] ?? 99;
    const bPriority = STATUS_PRIORITY[bv] ?? 99;
    return aPriority - bPriority;
  }

  if (NUMERIC_SORT_KEYS.includes(key)) {
    return Number(bv) - Number(av);
  }

  return String(av).localeCompare(String(bv));
}

function getTagPriority(row, tagLog) {
  const key = getRowTagKey(row);
  const tags = tagLog?.[key];
  if (!tags) return 3;
  if (tags.bug) return TAG_PRIORITY.bug;
  if (tags.aso) return TAG_PRIORITY.aso;
  if (tags.baseline) return TAG_PRIORITY.baseline;
  return 3;
}

export function filteredSorted(store, tagLog = {}) {
  const q = store.q.trim().toLowerCase();
  let out = store.rows;

  if (store.status) out = out.filter(r => r.status === store.status);
  if (store.viewport) out = out.filter(r => r.viewport === store.viewport);
  if (store.browser) out = out.filter(r => r.browser === store.browser);

  if (q) {
    out = out.filter(r =>
      (r.scenario_id || "").toLowerCase().includes(q) ||
      (r.message || "").toLowerCase().includes(q)
    );
  }

  const key = store.sortKey;

  if (key === "tags") {
    out = [...out].sort((a, b) => {
      const aPriority = getTagPriority(a, tagLog);
      const bPriority = getTagPriority(b, tagLog);
      if (aPriority !== bPriority) return aPriority - bPriority;
      return String(a.scenario_id || "").localeCompare(String(b.scenario_id || ""));
    });
    return out;
  }

  out = [...out].sort((a, b) => compareValues(a[key], b[key], key));

  return out;
}

export function resetFilters(store) {
  store.q = "";
  store.status = "";
  store.viewport = "";
  store.browser = "";
  store.sortKey = "scenario_id";
}
