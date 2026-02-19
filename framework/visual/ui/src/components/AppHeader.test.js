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
    bootstrap: { name: "Bootstrap (Default)", dropdownGradient: "linear-gradient(135deg, #e8f4fd 0%, #f5f5f5 100%)" },
    dark: { name: "Dark", dropdownGradient: "linear-gradient(135deg, #3a3f47 0%, #2d3238 100%)" },
    dracula: { name: "Dracula", dropdownGradient: "linear-gradient(135deg, #44475a 0%, #383a4e 100%)" },
    gruvbox: { name: "Gruvbox", dropdownGradient: "linear-gradient(135deg, #45403b 0%, #3c3836 100%)" },
    atom: { name: "Atom (One Dark)", dropdownGradient: "linear-gradient(135deg, #2c313a 0%, #21252b 100%)" },
    nord: { name: "Nord", dropdownGradient: "linear-gradient(135deg, #d8dee9 0%, #e5e9f0 100%)" },
    solarized: { name: "Solarized Light", dropdownGradient: "linear-gradient(135deg, #eee8d5 0%, #f5efdc 100%)" },
    github: { name: "GitHub Light", dropdownGradient: "linear-gradient(135deg, #f6f8fa 0%, #ffffff 100%)" },
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
    
    const dropdown = wrapper.find(".theme-dropdown");
    expect(dropdown.exists()).toBe(true);
    
    const items = wrapper.findAll(".theme-dropdown .dropdown-item");
    expect(items).toHaveLength(8);
    expect(items[0].text()).toContain("Bootstrap (Default)");
    expect(items[1].text()).toContain("Dark");
  });

  it("renders language selector with flag buttons", async () => {
    const wrapper = mount(AppHeader);
    await flushPromises();
    
    const buttons = wrapper.findAll(".language-selector button");
    expect(buttons).toHaveLength(3);
    expect(buttons[0].text()).toBe("🇬🇧");
    expect(buttons[1].text()).toBe("🇵🇱");
    expect(buttons[2].text()).toBe("🇺🇦");
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
