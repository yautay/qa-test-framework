export function fmt(v, digits = 6) {
  if (v === null || v === undefined || v === "") return "";
  const n = Number(v);
  if (!Number.isFinite(n)) return "";
  return n.toFixed(digits).replace(/0+$/,'').replace(/\.$/, '');
}

export function summaryFor(rows) {
  const total = rows.length;
  const normalizeStatus = (status) => {
    if (status === "new") return "failed";
    return status;
  };
  const by = (s) => rows.filter(r => normalizeStatus(r.status) === s).length;
  return {
    total,
    passed: by("passed"),
    failed: by("failed"),
    uncertain: by("uncertain"),
    skipped: by("skipped"),
  };
}
