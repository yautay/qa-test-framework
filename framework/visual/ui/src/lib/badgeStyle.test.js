import { describe, expect, it, vi } from "vitest";

vi.mock("./themes", () => ({
  currentTheme: { value: "bootstrap" },
  presets: {
    bootstrap: {
      primary: "#111111",
      secondary: "#222222",
      bodyColor: "#333333",
      badgeViewport: {
        default: { bg: "#aaaaaa", color: "#ffffff" },
        fhd: { bg: "#bbbbbb", color: "#000000" },
      },
      badgeBrowser: {
        default: { bg: "#cccccc", color: "#111111" },
        chrome: { bg: "#dddddd", color: "#222222" },
      },
    },
  },
}));

import { badgeStyle } from "./badgeStyle";

describe("badgeStyle", () => {
  it("uses exact palette match for known viewport", () => {
    expect(badgeStyle("viewport", "fhd")).toEqual({
      backgroundColor: "#bbbbbb",
      color: "#000000",
    });
  });

  it("falls back to palette defaults for unknown values", () => {
    expect(badgeStyle("browser", "unknown")).toEqual({
      backgroundColor: "#cccccc",
      color: "#111111",
    });
  });
});
