import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { presets } from "./themes/presets";

const STORAGE_KEY = "visual-report-theme";

describe("themes presets", () => {
  it("contains all expected theme presets", () => {
    expect(presets.bootstrap).toBeDefined();
    expect(presets.dark).toBeDefined();
    expect(presets.dracula).toBeDefined();
    expect(presets.gruvbox).toBeDefined();
    expect(presets.atom).toBeDefined();
  });

  it("each preset has all required properties", () => {
    const required = [
      "name",
      "primary",
      "secondary",
      "success",
      "danger",
      "warning",
      "onPrimary",
      "onSecondary",
      "onSuccess",
      "onDanger",
      "onWarning",
      "bodyBg",
      "bodyColor",
      "heroText",
      "heroMuted",
      "cardBg",
      "border",
      "textMuted",
      "runIdColor",
      "heroGradient",
    ];

    for (const [name, preset] of Object.entries(presets)) {
      for (const prop of required) {
        expect(preset[prop]).toBeDefined();
      }
    }
  });

  it("bootstrap is the default preset", () => {
    expect(presets.bootstrap.name).toBe("Bootstrap (Default)");
  });

  it("all presets have valid color values", () => {
    for (const [key, preset] of Object.entries(presets)) {
      expect(preset.primary).toMatch(/^#/);
      expect(preset.secondary).toMatch(/^#/);
      expect(preset.success).toMatch(/^#/);
      expect(preset.danger).toMatch(/^#/);
      expect(preset.warning).toMatch(/^#/);
      expect(preset.bodyBg).toMatch(/^#/);
      expect(preset.bodyColor).toMatch(/^#/);
      expect(preset.cardBg).toMatch(/^#/);
    }
  });
});

describe("theme application", () => {
  let setAttributeSpy;
  let setPropertySpy;
  let localStorageData;
  let mockDocument;
  let mockLocalStorage;

  beforeEach(() => {
    setAttributeSpy = vi.fn();
    setPropertySpy = vi.fn((key, value) => {});

    localStorageData = {};
    mockLocalStorage = {
      getItem: vi.fn((key) => localStorageData[key] || null),
      setItem: vi.fn((key, value) => { localStorageData[key] = value; }),
    };

    mockDocument = {
      createElement: vi.fn(() => ({
        style: {},
        setAttribute: vi.fn(),
        remove: vi.fn(),
      })),
      documentElement: {
        style: {
          setProperty: setPropertySpy,
          removeProperty: vi.fn(),
        },
        setAttribute: setAttributeSpy,
      },
    };
  });

  afterEach(() => {
    vi.resetModules();
  });

  it("applies CSS variables when theme changes", async () => {
    vi.stubGlobal("document", mockDocument);
    vi.stubGlobal("localStorage", mockLocalStorage);

    const { setTheme, currentTheme } = await import("./themes/index");

    setTheme("dark");

    expect(setAttributeSpy).toHaveBeenCalledWith("data-theme", "dark");
    expect(setPropertySpy).toHaveBeenCalledWith("--primary", expect.any(String));
    expect(setPropertySpy).toHaveBeenCalledWith("--card-bg", expect.any(String));
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(STORAGE_KEY, "dark");
    expect(currentTheme.value).toBe("dark");
  });

  it("does not apply unknown theme", async () => {
    vi.stubGlobal("document", mockDocument);
    vi.stubGlobal("localStorage", mockLocalStorage);

    const { setTheme, currentTheme } = await import("./themes/index");

    const original = currentTheme.value;
    setTheme("nonexistent");

    expect(setAttributeSpy).not.toHaveBeenCalled();
    expect(currentTheme.value).toBe(original);
  });

  it("applies all CSS variables from preset", async () => {
    vi.stubGlobal("document", mockDocument);
    vi.stubGlobal("localStorage", mockLocalStorage);

    const { setTheme } = await import("./themes/index");

    setTheme("dracula");

    const callArgs = setPropertySpy.mock.calls.map(c => c[0]);
    expect(callArgs).toContain("--primary");
    expect(callArgs).toContain("--secondary");
    expect(callArgs).toContain("--success");
    expect(callArgs).toContain("--danger");
    expect(callArgs).toContain("--warning");
    expect(callArgs).toContain("--on-primary");
    expect(callArgs).toContain("--on-secondary");
    expect(callArgs).toContain("--on-success");
    expect(callArgs).toContain("--on-danger");
    expect(callArgs).toContain("--on-warning");
    expect(callArgs).toContain("--body-bg");
    expect(callArgs).toContain("--body-color");
    expect(callArgs).toContain("--hero-text");
    expect(callArgs).toContain("--hero-muted");
    expect(callArgs).toContain("--card-bg");
    expect(callArgs).toContain("--border");
    expect(callArgs).toContain("--text-muted");
    expect(callArgs).toContain("--run-id-color");
    expect(callArgs).toContain("--hero-gradient");
  });
});
