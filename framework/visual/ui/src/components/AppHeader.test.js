import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { ref } from "vue";

import AppHeader from "./AppHeader.vue";

vi.mock("../lib/i18n", () => ({
  locale: ref("en"),
  setLocale: vi.fn(),
}));

vi.mock("../lib/themes", () => ({
  currentTheme: ref("bootstrap"),
  setTheme: vi.fn(),
  presets: {
    bootstrap: { name: "Bootstrap (Default)" },
    dark: { name: "Dark" },
    dracula: { name: "Dracula" },
    gruvbox: { name: "Gruvbox" },
    atom: { name: "Atom (One Dark)" },
  },
}));

describe("AppHeader", () => {
  function flushPromises() {
    return new Promise((resolve) => {
      setTimeout(resolve, 0);
    });
  }

  it("renders theme selector with all presets", async () => {
    const wrapper = mount(AppHeader);
    await flushPromises();
    
    const select = wrapper.find("select.theme-select");
    expect(select.exists()).toBe(true);
    
    const options = wrapper.findAll("select.theme-select option");
    expect(options).toHaveLength(5);
    expect(options[0].text()).toBe("Bootstrap (Default)");
    expect(options[1].text()).toBe("Dark");
  });

  it("renders language selector with flag buttons", async () => {
    const wrapper = mount(AppHeader);
    await flushPromises();
    
    const buttons = wrapper.findAll(".language-selector button");
    expect(buttons).toHaveLength(2);
    expect(buttons[0].text()).toBe("🇬🇧");
    expect(buttons[1].text()).toBe("🇵🇱");
  });

  it("displays datetime", async () => {
    const wrapper = mount(AppHeader);
    await flushPromises();
    
    const datetime = wrapper.find(".datetime");
    expect(datetime.exists()).toBe(true);
    expect(datetime.text()).toMatch(/\d{2}\.\d{2}\.\d{4},? \d{2}:\d{2}/);
  });

  it("has correct CSS classes for styling", async () => {
    const wrapper = mount(AppHeader);
    await flushPromises();
    
    const header = wrapper.find(".app-header");
    expect(header.exists()).toBe(true);
    expect(header.classes()).toContain("mb-3");
    expect(header.classes()).toContain("p-3");
    expect(header.classes()).toContain("rounded-4");
  });
});
