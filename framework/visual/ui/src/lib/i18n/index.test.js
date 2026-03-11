import { beforeEach, describe, expect, it, vi } from "vitest";
import { locale, setLocale, syncLocaleFromStorage, t } from "./index";

const STORAGE_KEY = "visual-report-locale";

describe("i18n", () => {
  beforeEach(() => {
    window.localStorage.clear();
    syncLocaleFromStorage();
  });

  it("falls back to english for unsupported saved locale", () => {
    window.localStorage.setItem(STORAGE_KEY, "de");
    syncLocaleFromStorage();

    expect(locale.value).toBe("en");
    expect(t("hero.title")).toBe("Artifacts Dashboard");
  });

  it("uses saved locale when it is supported", () => {
    window.localStorage.setItem(STORAGE_KEY, "pl");
    syncLocaleFromStorage();

    expect(locale.value).toBe("pl");
    expect(t("hero.title")).toBe("Dashboard Raportów");
  });

  it("resolves sync and language tooltip keys in all supported locales", () => {

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
