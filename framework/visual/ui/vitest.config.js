import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.js"],
    globals: true,
    coverage: {
      provider: "istanbul",
      reporter: ["text", "json", "html"],
      reportsDirectory: "coverage",
      include: ["src/**/*.{js,vue}"],
      exclude: [
        "src/**/*.test.js",
        "src/main.js",
        "src/App.vue",
      ],
      thresholds: {
        lines: 55,
        branches: 45,
        functions: 50,
        statements: 55,
      },
    },
  },
});
