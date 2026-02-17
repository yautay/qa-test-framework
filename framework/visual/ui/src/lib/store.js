import { summaryFor } from "./format";

export function createStore() {
  const data = (window.__VRT_RESULTS__ || {});
  const rows = (data.results || []);
  return {
    rows,
    q: "",
    status: "",
    mode: "",
    sortKey: "scenario_id",
    summary: summaryFor(rows),
  };
}

export function filteredSorted(store) {
  const q = store.q.trim().toLowerCase();
  let out = store.rows;

  if (store.status) out = out.filter(r => r.status === store.status);
  if (store.mode) out = out.filter(r => r.compare_mode === store.mode);

  if (q) {
    out = out.filter(r =>
      (r.scenario_id || "").toLowerCase().includes(q) ||
      (r.message || "").toLowerCase().includes(q)
    );
  }

  const key = store.sortKey;
  out = [...out].sort((a,b) => {
    const av = a[key]; const bv = b[key];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    if (typeof av === "number" && typeof bv === "number") return bv - av;
    return String(av).localeCompare(String(bv));
  });

  return out;
}

export function resetFilters(store) {
  store.q = "";
  store.status = "";
  store.mode = "";
  store.sortKey = "scenario_id";
}
