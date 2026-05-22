export default async function pythonVenvGuardPlugin() {
  const PLAIN_PYTHON_RE = /(^|[\s;&|])python(?:\d+(?:\.\d+)?)?\b/;
  const STANDALONE_PYTEST_RE = /(^|[\s;&|])pytest\b/;
  const STANDALONE_PIP_RE = /(^|[\s;&|])pip\b/;

  return {
    "tool.execute.before": async (_input, output) => {
      const toolName = output?.tool || output?.name;
      if (toolName !== "bash") {
        return;
      }

      const command = output?.args?.command;
      if (typeof command !== "string") {
        return;
      }

      const hasVenvPython = command.includes(".venv/bin/python");
      const hasPlainPython = PLAIN_PYTHON_RE.test(command);
      const hasStandalonePytest = STANDALONE_PYTEST_RE.test(command);
      const hasStandalonePip = STANDALONE_PIP_RE.test(command);

      if ((hasPlainPython && !hasVenvPython) || hasStandalonePytest || hasStandalonePip) {
        throw new Error(
          "Blocked by python-venv-guard: use `make <target>` or `.venv/bin/python -m ...` (never plain python/pytest/pip)."
        );
      }
    },
  };
}
