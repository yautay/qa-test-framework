import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { execSync } from "node:child_process";
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

function runGit(args) {
  try {
    return execSync(`git ${args.join(" ")}`, {
      cwd: repoRootDir,
      stdio: ["ignore", "pipe", "ignore"],
      encoding: "utf-8",
    }).trim();
  } catch (_error) {
    return "";
  }
}

function resolveVersionFromGit() {
  const raw = runGit(["describe", "--tags", "--always", "--dirty"]);
  if (!raw) return "unknown";
  return raw.startsWith("v") ? raw.slice(1) : raw;
}

function buildInfoPlugin() {
  return {
    name: "netqawner-build-info",
    closeBundle() {
      const payload = {
        version: resolveVersionFromGit(),
        codename: readCodenameFromPyproject(),
        commit: runGit(["rev-parse", "--short", "HEAD"]) || "unknown",
        built_at: new Date().toISOString(),
      };
      const outputPath = resolve(uiRootDir, "dist", "build-info.json");
      writeFileSync(outputPath, `${JSON.stringify(payload, null, 2)}\n`, "utf-8");
    },
  };
}

export default defineConfig({
  base: "./",
  plugins: [vue(), buildInfoPlugin()],
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
