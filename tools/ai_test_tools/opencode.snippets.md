# OpenCode Registration Snippets

Use these snippets in project `opencode.json`.

## Register skills path

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "paths": [
      "tools/ai_test_tools/skills"
    ]
  }
}
```

## Register command: /new_test_prepare

```json
{
  "command": {
    "new_test_prepare": {
      "description": "Prepare new E2E test blueprint from Playwright trace artifacts",
      "prompt": "Use skill new-test-prepare. Ask user for: scenario_name, target_domain, trace_zip_path, checkpoints_json_path, optional metadata_json_path. Analyze artifacts and repository context. Do not generate final test code. Keep host/domain environment-agnostic and avoid hardcoded base URLs. Focus on path semantics, business intent, stable locator strategy, and Arrange-Act-Assert blueprint. Return the mandatory output sections and ready/needs-input status."
    }
  }
}
```

## Register command: /new_test_generate

```json
{
  "command": {
    "new_test_generate": {
      "description": "Generate new E2E test code from prepare payload",
      "prompt": "Use skill new-test-generate. Consume generation_payload from /new_test_prepare and implement test code in this repository. Keep base hosts non-hardcoded, preserve repository contracts, put assertions in tests only, avoid sleeps and retry ladders, and use timeout constants. Reuse existing POM/flows/builders where possible."
    }
  }
}
```

## Optional command combo

You can merge both commands under one `command` object in your final `opencode.json`.

After editing config, restart opencode to load new commands/skills.
