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

  it("resolves sync and language tooltip keys in all supported locales", async () => {
    const { setLocale, t } = await import("./index");

    setLocale("en");
    expect(t("sync.pendingTooltip")).not.toBe("sync.pendingTooltip");
    expect(t("sync.unsyncedTooltip")).not.toBe("sync.unsyncedTooltip");
    expect(t("pms.pendingTest")).not.toBe("pms.pendingTest");
    expect(t("language.english")).not.toBe("language.english");

    setLocale("pl");
    expect(t("sync.pendingTooltip")).not.toBe("sync.pendingTooltip");
    expect(t("sync.unsyncedTooltip")).not.toBe("sync.unsyncedTooltip");
    expect(t("pms.pendingTest")).not.toBe("pms.pendingTest");
    expect(t("language.polish")).not.toBe("language.polish");

    setLocale("uk");
    expect(t("sync.pendingTooltip")).not.toBe("sync.pendingTooltip");
    expect(t("sync.unsyncedTooltip")).not.toBe("sync.unsyncedTooltip");
    expect(t("pms.pendingTest")).not.toBe("pms.pendingTest");
    expect(t("language.ukrainian")).not.toBe("language.ukrainian");
  });
});
