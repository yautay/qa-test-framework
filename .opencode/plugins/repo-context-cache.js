import { execSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

const CACHE_DIR = "artifacts/ai-test-tools";
const CACHE_FILE = "repo_map.json";
const ROOT_AGENTS = "AGENTS.md";

function safeRead(filePath) {
  try {
    return readFileSync(filePath, "utf-8");
  } catch {
    return "";
  }
}

function listTracked(repoRoot, pattern) {
  try {
    const out = execSync(`git ls-files "${pattern}"`, {
      cwd: repoRoot,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "ignore"],
    });
    return out
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
  } catch {
    return [];
  }
}

function detectKeyAreas(repoRoot) {
  return {
    e2e_tests: listTracked(repoRoot, "qa/e2e/netcorner/**/tests/**/*.py").slice(0, 80),
    page_objects: listTracked(repoRoot, "qa/e2e/netcorner/**/lib/page_objects/**/*.py").slice(0, 120),
    flows: listTracked(repoRoot, "qa/e2e/netcorner/**/lib/flows/**/*.py").slice(0, 120),
    test_data: listTracked(repoRoot, "qa/e2e/netcorner/**/lib/test_data/**/*.py").slice(0, 120),
    aso_tests: listTracked(repoRoot, "qa/aso/framework/**/*.py").slice(0, 80),
    visual_ui: listTracked(repoRoot, "framework/visual/ui/**/*").slice(0, 80),
  };
}

function collectNestedAgents(repoRoot) {
  return listTracked(repoRoot, "**/AGENTS.md")
    .filter((p) => p !== ROOT_AGENTS)
    .filter((p) => p.includes("qa/e2e/netcorner/"))
    .slice(0, 80);
}

function buildCache(repoRoot) {
  const gitSha = execSync("git rev-parse HEAD", {
    cwd: repoRoot,
    encoding: "utf-8",
    stdio: ["ignore", "pipe", "ignore"],
  }).trim();

  const rootAgents = safeRead(path.join(repoRoot, ROOT_AGENTS));
  const nestedAgents = collectNestedAgents(repoRoot);

  const payload = {
    schema_version: "1.0",
    generated_at_utc: new Date().toISOString(),
    git_sha: gitSha,
    root_agents_path: ROOT_AGENTS,
    root_agents_excerpt: rootAgents.split("\n").slice(0, 70).join("\n"),
    nested_agents_paths: nestedAgents,
    key_areas: detectKeyAreas(repoRoot),
    usage_hint:
      "Use this map first. Read full AGENTS.md files only for paths you modify. Prefer make/.venv commands and repository contracts.",
  };

  const dir = path.join(repoRoot, CACHE_DIR);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
  const cachePath = path.join(dir, CACHE_FILE);
  writeFileSync(cachePath, `${JSON.stringify(payload, null, 2)}\n`, "utf-8");
  return { cachePath, payload };
}

function loadOrBuildCache(repoRoot) {
  const cachePath = path.join(repoRoot, CACHE_DIR, CACHE_FILE);
  if (!existsSync(cachePath)) {
    return buildCache(repoRoot);
  }

  try {
    const ageMs = Date.now() - statSync(cachePath).mtimeMs;
    const staleByTime = ageMs > 30 * 60 * 1000;
    const currentSha = execSync("git rev-parse HEAD", {
      cwd: repoRoot,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
    const current = JSON.parse(readFileSync(cachePath, "utf-8"));
    const staleBySha = current.git_sha !== currentSha;

    if (staleByTime || staleBySha) {
      return buildCache(repoRoot);
    }
    return { cachePath, payload: current };
  } catch {
    return buildCache(repoRoot);
  }
}

function compactMap(payload) {
  const sample = (arr, n = 10) => (Array.isArray(arr) ? arr.slice(0, n) : []);
  return {
    git_sha: payload.git_sha,
    root_agents_path: payload.root_agents_path,
    nested_agents_paths_sample: sample(payload.nested_agents_paths, 16),
    key_areas_sample: {
      e2e_tests: sample(payload.key_areas?.e2e_tests, 14),
      page_objects: sample(payload.key_areas?.page_objects, 14),
      flows: sample(payload.key_areas?.flows, 14),
      test_data: sample(payload.key_areas?.test_data, 14),
      aso_tests: sample(payload.key_areas?.aso_tests, 14),
      visual_ui: sample(payload.key_areas?.visual_ui, 14),
    },
    usage_hint: payload.usage_hint,
  };
}

export default async function repoContextCachePlugin({ directory }) {
  return {
    "chat.system.transform": async (_input, output) => {
      try {
        const repoRoot = directory;
        const { cachePath, payload } = loadOrBuildCache(repoRoot);
        const compact = compactMap(payload);
        const appendix = [
          "",
          "[repo-context-cache]",
          `cache_file: ${path.relative(repoRoot, cachePath)}`,
          "Use this compact repository map to avoid broad rescans:",
          JSON.stringify(compact, null, 2),
        ].join("\n");

        if (typeof output.text === "string") {
          output.text = `${output.text}\n${appendix}`;
        }
      } catch {
        // Best-effort cache injection only.
      }
    },
  };
}
