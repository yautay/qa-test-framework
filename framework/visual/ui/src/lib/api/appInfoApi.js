import { parseJsonResponse } from "./parseJsonResponse";

export async function fetchAppInfo() {
  const response = await fetch("/api/app-info", { cache: "no-store" });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(payload?.error || "unable to fetch app info");
  }
  return payload && typeof payload === "object" ? payload : {};
}
