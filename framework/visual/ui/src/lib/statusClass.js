export function statusBadgeClass(status) {
  if (status === "passed") return "text-bg-success";
  if (status === "failed") return "text-bg-danger";
  if (status === "uncertain") return "text-bg-warning";
  if (status === "skipped" || status === "new") return "text-bg-warning";
  if (status === "error") return "text-bg-dark";
  return "";
}
