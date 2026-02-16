export function fmt(v, digits = 6) {
  if (v === null || v === undefined || v === "") return "";
  const n = Number(v);
  if (!Number.isFinite(n)) return "";
  // obetnij trailing zera
  return n.toFixed(digits).replace(/0+$/,'').replace(/\.$/,'');
}

export function summaryFor(rows) {
  const total = rows.length;
  const by = (s) => rows.filter(r => r.status === s).length;
  return `total=${total} passed=${by('passed')} failed=${by('failed')} skipped=${by('skipped')} error=${by('error')} new=${by('new')}`;
}
