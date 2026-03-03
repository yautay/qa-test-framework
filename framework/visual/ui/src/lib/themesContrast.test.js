import { describe, expect, it } from "vitest";

import { presets } from "./themes/presets";

function hexToRgb(hex) {
  const raw = String(hex).replace("#", "").trim();
  const normalized = raw.length === 3 ? raw.split("").map((char) => char + char).join("") : raw;
  const n = Number.parseInt(normalized, 16);
  return {
    r: (n >> 16) & 255,
    g: (n >> 8) & 255,
    b: n & 255,
    a: 1,
  };
}

function parseColor(value) {
  const color = String(value || "").trim();
  if (!color) return null;
  if (color.startsWith("#")) {
    return hexToRgb(color);
  }

  const match = color.match(/^rgba?\(([^)]+)\)$/i);
  if (!match) return null;
  const parts = match[1].split(",").map((item) => Number.parseFloat(item.trim()));
  if (parts.length < 3 || Number.isNaN(parts[0]) || Number.isNaN(parts[1]) || Number.isNaN(parts[2])) {
    return null;
  }

  return {
    r: parts[0],
    g: parts[1],
    b: parts[2],
    a: Number.isFinite(parts[3]) ? parts[3] : 1,
  };
}

function blend(foreground, background) {
  const alpha = Number.isFinite(foreground.a) ? foreground.a : 1;
  return {
    r: foreground.r * alpha + background.r * (1 - alpha),
    g: foreground.g * alpha + background.g * (1 - alpha),
    b: foreground.b * alpha + background.b * (1 - alpha),
    a: 1,
  };
}

function luminance(rgb) {
  const channel = (value) => {
    const c = value / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };

  return 0.2126 * channel(rgb.r) + 0.7152 * channel(rgb.g) + 0.0722 * channel(rgb.b);
}

function contrastRatio(foregroundColor, backgroundColor) {
  const foreground = parseColor(foregroundColor);
  const background = parseColor(backgroundColor);
  if (!foreground || !background) return Number.NaN;

  const renderedForeground = foreground.a < 1 ? blend(foreground, background) : foreground;
  const l1 = luminance(renderedForeground);
  const l2 = luminance(background);
  const [maxL, minL] = l1 >= l2 ? [l1, l2] : [l2, l1];
  return (maxL + 0.05) / (minL + 0.05);
}

function gradientStops(gradient) {
  return String(gradient || "").match(/#[0-9a-fA-F]{3,8}/g) || [];
}

describe("theme accessibility contrast", () => {
  it("keeps semantic token pairs at AA level", () => {
    const pairs = [
      ["onPrimary", "primary"],
      ["onSecondary", "secondary"],
      ["onSuccess", "success"],
      ["onDanger", "danger"],
      ["onWarning", "warning"],
      ["bodyColor", "bodyBg"],
    ];

    for (const [themeName, preset] of Object.entries(presets)) {
      for (const [foregroundToken, backgroundToken] of pairs) {
        const ratio = contrastRatio(preset[foregroundToken], preset[backgroundToken]);
        expect(
          ratio,
          `${themeName}: ${foregroundToken} on ${backgroundToken} should be >= 4.5, got ${ratio.toFixed(2)}`,
        ).toBeGreaterThanOrEqual(4.5);
      }
    }
  });

  it("keeps hero title text readable across hero gradient stops", () => {
    for (const [themeName, preset] of Object.entries(presets)) {
      const stops = gradientStops(preset.heroGradient);
      expect(stops.length, `${themeName}: heroGradient should include color stops`).toBeGreaterThan(0);

      for (const stop of stops) {
        const ratio = contrastRatio(preset.heroText, stop);
        expect(
          ratio,
          `${themeName}: heroText on ${stop} should be >= 4.5, got ${ratio.toFixed(2)}`,
        ).toBeGreaterThanOrEqual(4.5);
      }
    }
  });

  it("keeps hero muted text readable across hero gradient stops", () => {
    for (const [themeName, preset] of Object.entries(presets)) {
      const stops = gradientStops(preset.heroGradient);
      expect(stops.length, `${themeName}: heroGradient should include color stops`).toBeGreaterThan(0);

      for (const stop of stops) {
        const ratio = contrastRatio(preset.heroMuted, stop);
        expect(
          ratio,
          `${themeName}: heroMuted on ${stop} should be >= 3.0, got ${ratio.toFixed(2)}`,
        ).toBeGreaterThanOrEqual(3);
      }
    }
  });
});
