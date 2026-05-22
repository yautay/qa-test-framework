function extractPatchedPaths(patchText) {
  const paths = [];
  const lines = patchText.split("\n");
  for (const line of lines) {
    if (line.startsWith("*** Update File: ")) {
      paths.push(line.replace("*** Update File: ", "").trim());
    } else if (line.startsWith("*** Add File: ")) {
      paths.push(line.replace("*** Add File: ", "").trim());
    }
  }
  return paths;
}

function collectAddedLines(patchText) {
  const added = [];
  const lines = patchText.split("\n");
  for (const line of lines) {
    if (line.startsWith("+") && !line.startsWith("+++")) {
      added.push(line.slice(1));
    }
  }
  return added.join("\n");
}

export default async function e2eAntiPatternGuardPlugin() {
  const SLEEP_RE = /\bsleep\s*\(/;
  const WAIT_TIMEOUT_RE = /\bwait_for_timeout\s*\(/;
  const RAW_TIMEOUT_RE = /\b(timeout|timeout_ms|timeout_s)\s*=\s*\d{4,}\b/;

  return {
    "tool.execute.before": async (_input, output) => {
      const toolName = output?.tool || output?.name;
      if (toolName !== "apply_patch") {
        return;
      }

      const patchText = output?.args?.patchText;
      if (typeof patchText !== "string") {
        return;
      }

      const touchedPaths = extractPatchedPaths(patchText);
      const touchesE2E = touchedPaths.some((p) => p.includes("qa/e2e/"));
      if (!touchesE2E) {
        return;
      }

      const addedCode = collectAddedLines(patchText);
      if (SLEEP_RE.test(addedCode) || WAIT_TIMEOUT_RE.test(addedCode)) {
        throw new Error(
          "Blocked by e2e-anti-pattern-guard: do not add sleep(...) or wait_for_timeout(...) in E2E code."
        );
      }

      if (RAW_TIMEOUT_RE.test(addedCode)) {
        throw new Error(
          "Blocked by e2e-anti-pattern-guard: do not add raw timeout literals; use named timeout constants."
        );
      }
    },
  };
}
