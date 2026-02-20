import { beforeEach, describe, expect, it, vi } from "vitest";

const STORAGE_KEY = "visual-report-locale";

describe("i18n", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.resetModules();
  });

  it("falls back to english for unsupported saved locale", async () => {
    window.localStorage.setItem(STORAGE_KEY, "de");

    const { locale, t } = await import("./index");

    expect(locale.value).toBe("en");
    expect(t("hero.title")).toBe("Artifacts Dashboard");
  });

  it("uses saved locale when it is supported", async () => {
    window.localStorage.setItem(STORAGE_KEY, "pl");

    const { locale, t } = await import("./index");

    expect(locale.value).toBe("pl");
    expect(t("hero.title")).toBe("Dashboard Raportów");
  });
});
