import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";

import HeroPage from "./HeroPage.vue";

vi.mock("../lib/api/reportsApi", () => ({
  fetchReportsList: vi.fn(async () => [
    {
      run_id: "20260218_120000_000001",
      total: 5,
      passed: 3,
      failed: 2,
      new: 0,
      summary: "failed=2 passed=3 new=0",
      updated_at: "2026-02-18 12:00:00",
    },
    {
      run_id: "20260217_120000_000001",
      total: 4,
      passed: 4,
      failed: 0,
      new: 0,
      summary: "failed=0 passed=4 new=0",
      updated_at: "2026-02-17 12:00:00",
    },
  ]),
}));

function flushPromises() {
  return new Promise((resolve) => {
    setTimeout(resolve, 0);
  });
}

describe("HeroPage", () => {
  it("loads reports and filters by query", async () => {
    const wrapper = mount(HeroPage);
    await flushPromises();

    expect(wrapper.text()).toContain("20260218_120000_000001");
    expect(wrapper.text()).toContain("20260217_120000_000001");

    const input = wrapper.find("input");
    await input.setValue("failed=2");

    expect(wrapper.text()).toContain("20260218_120000_000001");
    expect(wrapper.text()).not.toContain("20260217_120000_000001");
  });
});
