export function getRowTagKey(row) {
  return [
    row?.scenario_id || "",
    row?.actual_path || "",
    row?.baseline_path || "",
    row?.diff_path || "",
  ].join("::");
}
