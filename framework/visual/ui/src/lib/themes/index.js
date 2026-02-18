import { ref, watch } from "vue";
import { presets } from "./presets";

const STORAGE_KEY = "visual-report-theme";

const savedTheme =
  typeof window !== "undefined"
    ? window.localStorage.getItem(STORAGE_KEY)
    : null;

const currentTheme = ref(savedTheme || "bootstrap");

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
  root.style.setProperty("--body-bg", preset.bodyBg);
  root.style.setProperty("--body-color", preset.bodyColor);
  root.style.setProperty("--card-bg", preset.cardBg);
  root.style.setProperty("--border", preset.border);
  root.style.setProperty("--text-muted", preset.textMuted);
  root.style.setProperty("--hero-gradient", preset.heroGradient);
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
