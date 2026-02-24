import { parseJsonResponse } from "./parseJsonResponse";

export async function fetchPerceptualQueue() {
  const response = await fetch("/api/perceptual/queue", { cache: "no-store" });
  const payload = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error(payload?.error || payload?.error_message || "unable to fetch perceptual queue");
  }
  return payload && typeof payload === "object" ? payload : {};
}
