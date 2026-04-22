import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const uiRootDir = fileURLToPath(new URL(".", import.meta.url));
const repoRootDir = resolve(uiRootDir, "../../..");

function readCodenameFromPyproject() {
  try {
    const pyprojectPath = resolve(repoRootDir, "pyproject.toml");
    const text = readFileSync(pyprojectPath, "utf-8");
    const match = text.match(/^codename\s*=\s*"([^"]+)"\s*$/m);
    return (match && match[1] ? match[1] : "unknown").trim() || "unknown";
  } catch (_error) {
    return "unknown";
  }
}

function readUiSrcVersion() {
  try {
    const packageJsonPath = resolve(uiRootDir, "package.json");
    const raw = JSON.parse(readFileSync(packageJsonPath, "utf-8"));
    return String(raw?.version || "").trim() || "unknown";
  } catch (_error) {
    return "unknown";
  }
}

function buildInfoPlugin() {
  return {
    name: "netqawner-build-info",
    closeBundle() {
      const uiSrcVersion = readUiSrcVersion();
      const payload = {
        version: uiSrcVersion,
        codename: readCodenameFromPyproject(),
        ui_src_version: uiSrcVersion,
      };
      const outputPath = resolve(uiRootDir, "dist", "build-info.json");
      writeFileSync(outputPath, `${JSON.stringify(payload, null, 2)}\n`, "utf-8");
    },
  };
}

export default defineConfig({
  base: "./",
  plugins: [vue({ devtools: true }), buildInfoPlugin()],
  build: {
    outDir: "dist",
    assetsDir: "assets",
    manifest: false,
    rollupOptions: {
      output: {
        entryFileNames: "assets/[name]-[hash].js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash][extname]"
      }
    }
  }
});
