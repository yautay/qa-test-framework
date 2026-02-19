import { describe, expect, it } from "vitest";

import { statusBadgeClass } from "./statusClass";

describe("statusBadgeClass", () => {
  it("returns success class for passed status", () => {
    expect(statusBadgeClass("passed")).toBe("text-bg-success");
  });

  it("returns danger class for failed status", () => {
    expect(statusBadgeClass("failed")).toBe("text-bg-danger");
  });

  it("returns warning class for uncertain status", () => {
    expect(statusBadgeClass("uncertain")).toBe("text-bg-warning");
  });

  it("returns warning class for skipped status", () => {
    expect(statusBadgeClass("skipped")).toBe("text-bg-warning");
  });

  it("returns warning class for new status", () => {
    expect(statusBadgeClass("new")).toBe("text-bg-warning");
  });

  it("returns dark class for error status", () => {
    expect(statusBadgeClass("error")).toBe("text-bg-dark");
  });

  it("returns empty string for unknown status", () => {
    expect(statusBadgeClass("unknown")).toBe("");
  });
});
