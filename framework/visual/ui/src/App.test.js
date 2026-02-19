import { afterEach, describe, expect, it } from "vitest";
import { shallowMount } from "@vue/test-utils";
import { nextTick } from "vue";

import App from "./App.vue";

function setPath(pathname) {
  window.history.pushState({}, "", pathname);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

describe("App runtime routing", () => {
  afterEach(() => {
    setPath("/");
  });

  it("updates report run id when path changes", async () => {
    setPath("/");
    const wrapper = shallowMount(App);

    expect(wrapper.findComponent({ name: "HeroPage" }).exists()).toBe(true);

    setPath("/reports/run-1");
    await nextTick();

    let reportPage = wrapper.findComponent({ name: "ReportPage" });
    expect(reportPage.exists()).toBe(true);
    expect(reportPage.props("runId")).toBe("run-1");

    setPath("/reports/run-2");
    await nextTick();

    reportPage = wrapper.findComponent({ name: "ReportPage" });
    expect(reportPage.props("runId")).toBe("run-2");
  });
});
