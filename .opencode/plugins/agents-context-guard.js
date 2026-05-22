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

function normalizePath(value) {
  return String(value || "").replaceAll("\\", "/");
}

export default async function agentsContextGuardPlugin() {
  const readAgentsPaths = new Set();
  const ROOT_AGENTS = "AGENTS.md";

  const domainGuides = {
    nuxt: "qa/e2e/netcorner/nuxt/pl/",
    admin: "qa/e2e/netcorner/admin/",
    mailhog: "qa/e2e/netcorner/mailhog/",
  };

  function inferDomain(paths) {
    for (const path of paths) {
      const p = normalizePath(path);
      if (p.includes("qa/e2e/netcorner/nuxt/")) return "nuxt";
      if (p.includes("qa/e2e/netcorner/admin/")) return "admin";
      if (p.includes("qa/e2e/netcorner/mailhog/")) return "mailhog";
    }
    return null;
  }

  return {
    "tool.execute.after": async (input) => {
      const toolName = input?.tool || input?.name;
      if (toolName !== "read") {
        return;
      }

      const filePath = normalizePath(input?.args?.filePath);
      if (!filePath.endsWith("AGENTS.md")) {
        return;
      }

      readAgentsPaths.add(filePath);
      if (filePath.endsWith("/qa-test-netquarner/AGENTS.md") || filePath === "AGENTS.md") {
        readAgentsPaths.add(ROOT_AGENTS);
      }
    },

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
      const domain = inferDomain(touchedPaths);
      if (!domain) {
        return;
      }

      const hasRoot = readAgentsPaths.has(ROOT_AGENTS) ||
        Array.from(readAgentsPaths).some((p) => normalizePath(p).endsWith("/qa-test-netquarner/AGENTS.md"));
      const requiredPrefix = domainGuides[domain];
      const hasNested = Array.from(readAgentsPaths).some((p) => normalizePath(p).includes(requiredPrefix));

      if (!hasRoot || !hasNested) {
        throw new Error(
          `Blocked by agents-context-guard: before editing ${domain} E2E files, read root AGENTS.md and nested AGENTS.md under ${requiredPrefix}`
        );
      }
    },
  };
}
