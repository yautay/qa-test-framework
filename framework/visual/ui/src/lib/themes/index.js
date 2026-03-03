import { ref } from "vue";
import { presets } from "./presets";

const STORAGE_KEY = "visual-report-theme";

const savedTheme =
  typeof window !== "undefined"
    ? window.localStorage.getItem(STORAGE_KEY) || null
    : null;

const currentTheme = ref(presets[savedTheme] ? savedTheme : "bootstrap");

function applyTheme(name) {
  if (typeof document === "undefined") return;

  const preset = presets[name];
  if (!preset) return;

  const root = document.documentElement;
  root.setAttribute("data-theme", name);

  root.style.setProperty("--primary", preset.primary);
  root.style.setProperty("--secondary", preset.secondary);
  root.style.setProperty("--success", preset.success);
  root.style.setProperty("--danger", preset.danger);
  root.style.setProperty("--warning", preset.warning);
  root.style.setProperty("--on-primary", preset.onPrimary || "#ffffff");
  root.style.setProperty("--on-secondary", preset.onSecondary || "#ffffff");
  root.style.setProperty("--on-success", preset.onSuccess || "#ffffff");
  root.style.setProperty("--on-danger", preset.onDanger || "#ffffff");
  root.style.setProperty("--on-warning", preset.onWarning || preset.bodyColor);
  root.style.setProperty("--body-bg", preset.bodyBg);
  root.style.setProperty("--body-color", preset.bodyColor);
  root.style.setProperty("--hero-text", preset.heroText || preset.bodyColor);
  root.style.setProperty("--hero-muted", preset.heroMuted || preset.textMuted);
  root.style.setProperty("--card-bg", preset.cardBg);
  root.style.setProperty("--border", preset.border);
  root.style.setProperty("--text-muted", preset.textMuted);
  root.style.setProperty("--run-id-color", preset.runIdColor || preset.primary);
  root.style.setProperty("--hero-gradient", preset.heroGradient);
  root.style.setProperty(
    "--dropdown-gradient",
    preset.dropdownGradient || preset.heroGradient || "transparent"
  );
  root.style.setProperty("--success-subtle", preset.successSubtle);
  root.style.setProperty("--danger-subtle", preset.dangerSubtle);
  root.style.setProperty("--warning-subtle", preset.warningSubtle);
  root.style.setProperty("--success-emphasis", preset.successEmphasis);
  root.style.setProperty("--danger-emphasis", preset.dangerEmphasis);
  root.style.setProperty("--warning-emphasis", preset.warningEmphasis);

  const viewportPalette = preset.badgeViewport || {};
  const browserPalette = preset.badgeBrowser || {};
  const filterHighlight = preset.filterHighlight || {};

  root.style.setProperty(
    "--badge-viewport-bg",
    viewportPalette.default?.bg || preset.secondary
  );
  root.style.setProperty(
    "--badge-viewport-color",
    viewportPalette.default?.color || preset.bodyColor
  );
  root.style.setProperty(
    "--badge-browser-bg",
    browserPalette.default?.bg || preset.secondary
  );
  root.style.setProperty(
    "--badge-browser-color",
    browserPalette.default?.color || preset.bodyColor
  );
  root.style.setProperty(
    "--filter-highlight-bg",
    filterHighlight.bg || "rgba(13, 110, 253, 0.12)"
  );
  root.style.setProperty(
    "--filter-highlight-border",
    filterHighlight.border || preset.primary
  );
  root.style.setProperty(
    "--filter-highlight-color",
    filterHighlight.color || preset.bodyColor
  );
}

export function initTheme() {
  applyTheme(currentTheme.value);
}

export function setTheme(name) {
  if (presets[name]) {
    currentTheme.value = name;
    applyTheme(name);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, name);
    }
  }
}

export { currentTheme, presets };
