import { currentTheme, presets } from "./themes";

export function badgeStyle(type, value) {
  const preset = presets[currentTheme.value] || presets.bootstrap;
  const key = type === "browser" ? "badgeBrowser" : "badgeViewport";
  const palette = preset[key] || {};
  const normalized = String(value || "").trim().toLowerCase();
  const entry = normalized && palette[normalized] ? palette[normalized] : palette.default;
  const fallbackBg = type === "browser" ? preset.secondary : preset.primary;
  const bg = (entry && entry.bg) || (palette.default && palette.default.bg) || fallbackBg;
  const color = (entry && entry.color) || (palette.default && palette.default.color) || preset.bodyColor;
  return {
    backgroundColor: bg,
    color,
  };
}
