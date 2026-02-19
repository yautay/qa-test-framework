import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { setActivePinia, createPinia } from "pinia";

import HeroPage from "./HeroPage.vue";

vi.mock("../lib/api/reportsApi", () => ({
  fetchReportsList: vi.fn(async () => [
    {
      run_id: "20260218_120000_000001",
      total: 5,
      passed: 3,
      failed: 2,
      summary: "failed=2 passed=3",
      tester: "jan.k",
      run_note: "manual smoke",
    },
    {
      run_id: "20260217_120000_000001",
      total: 4,
      passed: 4,
      failed: 0,
      summary: "failed=0 passed=4",
      tester: "ola.z",
      run_note: "",
    },
  ]),
}));

describe("HeroPage", () => {
  let pinia;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    vi.clearAllMocks();
  });

  it("loads reports on mount", async () => {
    const wrapper = mount(HeroPage, {
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.text()).toContain("20260218_120000_000001");
    expect(wrapper.text()).toContain("20260217_120000_000001");

    wrapper.unmount();
  });

  it("filters reports by query", async () => {
    const wrapper = mount(HeroPage, {
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    const input = wrapper.find("input");
    await input.setValue("failed=2");

    expect(wrapper.text()).toContain("20260218_120000_000001");
    expect(wrapper.text()).not.toContain("20260217_120000_000001");

    wrapper.unmount();
  });

  it("filters reports by tester select", async () => {
    const wrapper = mount(HeroPage, {
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    const selects = wrapper.findAll("select");
    const select = selects[selects.length - 1];
    await select.setValue("ola.z");

    expect(wrapper.text()).toContain("20260217_120000_000001");
    expect(wrapper.text()).not.toContain("20260218_120000_000001");

    wrapper.unmount();
  });

  it("displays total count in header", async () => {
    const wrapper = mount(HeroPage, {
      global: { plugins: [pinia] },
    });

    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(wrapper.text()).toContain("2");

    wrapper.unmount();
  });
});
