import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { ref } from "vue";

import AppHeader from "./AppHeader.vue";
import { fetchAppInfo } from "../lib/api/appInfoApi";
import { fetchPerceptualHealth } from "../lib/api/perceptualApi";

vi.mock("../lib/api/appInfoApi", () => ({
  fetchAppInfo: vi.fn(async () => ({
    runtime: { version: "1.2.3", codename: "San Eskobar", commit: "abc1234" },
    ui_build: {
      version: "1.2.2",
      codename: "San Eskobar",
      ui_src_version: "1.0.0",
      commit: "def5678",
      built_at: "2026-02-22T10:00:00Z",
    },
  })),
}));

vi.mock("../lib/api/perceptualApi", () => ({
  fetchPerceptualHealth: vi.fn(async () => ({
    ok: true,
    status_code: 200,
    checked_at_epoch: 1766600000,
    error_message: null,
    payload: {
      status: "ok",
      device: "cpu",
      metrics: ["dists", "lpips"],
      job_store: { backend: "redis", available: true },
      git: { tag: "v1.3-1-g951d06b" },
    },
  })),
}));

vi.mock("../lib/i18n", () => ({
  locale: ref("en"),
  setLocale: vi.fn(),
  t: (key) => {
    const labels = {
      "appInfo.ariaLabel": "Application build info",
      "appInfo.runtime": "Runtime",
      "appInfo.uiBuild": "UI build",
      "appInfo.uiSrcVersion": "ui src version",
      "appInfo.weekendCountdownPrefix": "Time until weekend starts",
      "appInfo.pmsHealth": "PMS health",
      "appInfo.status": "status",
      "appInfo.http": "http",
      "appInfo.device": "device",
      "appInfo.metrics": "metrics",
      "appInfo.jobStore": "job store",
      "appInfo.git": "git",
      "appInfo.lastCheck": "last check",
      "appInfo.healthDetail": "health detail",
      "appInfo.pmsDisabled": "PMS integration is disabled in the application configuration",
      "appInfo.pmsBaseUrlMissing": "PMS base URL is missing",
      "appInfo.pmsUnreachable": "PMS API is unreachable",
      "appInfo.error": "error",
      "appInfo.days": "days",
      "appInfo.hours": "hours",
      "appInfo.minutes": "minutes",
      "appInfo.seconds": "seconds",
    };
    return labels[key] || key;
  },
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
  beforeEach(() => {
    vi.clearAllMocks();
  });

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
    expect(datetime.text()).toMatch(/\d{2}\.\d{2}\.\d{4},? \d{2}:\d{2} (?:[A-Z]{3,5}|GMT[+-]\d{1,2})/);
  });

  it("renders weekend countdown in datetime tooltip", async () => {
    const wrapper = mount(AppHeader);
    await flushPromises();

    const tooltip = wrapper.find(".datetime-tooltip-content");
    expect(tooltip.exists()).toBe(true);
    expect(tooltip.text()).toContain("Time until weekend starts");
    expect(tooltip.text()).toMatch(/\d+ days, \d+ hours, \d+ minutes, \d+ seconds/);
  });

  it("renders app info icon with tooltip", async () => {
    const wrapper = mount(AppHeader);
    await flushPromises();

    const infoIcon = wrapper.find(".app-info");
    expect(infoIcon.exists()).toBe(true);
    expect(infoIcon.attributes("aria-label")).toBe("Application build info");

    const tooltip = wrapper.find(".app-info-tooltip");
    expect(tooltip.exists()).toBe(true);
    expect(tooltip.text()).toContain("Runtime");
    expect(tooltip.text()).toContain("UI build");
    expect(tooltip.text()).toContain("ui src version: 1.0.0");
    expect(tooltip.text()).toContain("PMS health");
    expect(tooltip.text()).toContain("status: ok");
    expect(tooltip.text()).toContain("http: 200");
    expect(tooltip.text()).toContain("device: cpu");
    expect(tooltip.text()).toContain("job store: redis (available)");
    expect(tooltip.text()).toContain("git: v1.3-1-g951d06b");
  });

  it("renders Polish codename with diacritics in tooltip", async () => {
    fetchAppInfo.mockResolvedValueOnce({
      runtime: { version: "1.2.3", codename: "Łódź Bałuty", commit: "abc1234" },
      ui_build: {
        version: "1.2.2",
        codename: "Łódź Bałuty",
        ui_src_version: "1.0.0",
        commit: "def5678",
        built_at: "2026-02-22T10:00:00Z",
      },
    });

    const wrapper = mount(AppHeader);
    await flushPromises();

    const tooltip = wrapper.find(".app-info-tooltip").text();
    expect(tooltip).toContain("codename: Łódź Bałuty");
  });

  it("marks app info icon red when PMS health fails", async () => {
    fetchPerceptualHealth.mockRejectedValueOnce(new Error("timeout"));
    const wrapper = mount(AppHeader);
    await flushPromises();

    const infoIcon = wrapper.find(".app-info");
    expect(infoIcon.classes()).toContain("app-info-error");
    expect(wrapper.find(".app-info-tooltip").text()).toContain("error: timeout");
  });

  it("shows explicit disabled reason when PMS is disabled", async () => {
    fetchPerceptualHealth.mockResolvedValueOnce({
      ok: false,
      status_code: 0,
      checked_at_epoch: 1766600000,
      reason_code: "pms_disabled",
      error_message: "PMS disabled in settings.py",
      payload: {},
    });

    const wrapper = mount(AppHeader);
    await flushPromises();

    const infoIcon = wrapper.find(".app-info");
    expect(infoIcon.classes()).not.toContain("app-info-error");

    const tooltip = wrapper.find(".app-info-tooltip").text();
    expect(tooltip).toContain("PMS integration is disabled in the application configuration");
    expect(tooltip).not.toContain("status:");
    expect(tooltip).not.toContain("error:");
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
