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
      "prompt": "Use skill new-test-prepare. Ask user for: scenario_name, target_domain, trace_zip_path, checkpoints_json_path, optional metadata_json_path. Before any planning, read repository guidance in AGENTS.md at repo root and all relevant nested AGENTS.md files for the target domain/path; treat them as mandatory source of truth and list exactly which guides were used. Analyze artifacts and repository context. Do not generate final test code. Keep host/domain environment-agnostic and avoid hardcoded base URLs. Focus on path semantics, business intent, stable locator strategy, and Arrange-Act-Assert blueprint. Return deterministic mandatory output sections in fixed order, create generation_payload JSON, and save it to thoughts/ai_gen/prepared/ for handoff to /new_test_generate."
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
      "prompt": "Use skill new-test-generate. Consume generation_payload or generation_payload_path from /new_test_prepare and implement test code in this repository. Prefer payload file path when provided. Before code changes, read repository guidance in AGENTS.md at repo root and all relevant nested AGENTS.md files for the target domain/path; treat them as mandatory source of truth and list exactly which guides were used. Before implementation, confirm with user: test name, marker set, severity, and target file path strategy. Keep base hosts non-hardcoded, preserve repository contracts, put assertions in tests only, avoid sleeps and retry ladders, and use timeout constants. Reuse existing POM/flows/builders where possible."
    }
  }
}
```

## Optional command combo

You can merge both commands under one `command` object in your final `opencode.json`.

## Register command: /new_test_suite_prepare

```json
{
  "command": {
    "new_test_suite_prepare": {
      "description": "Research and prepare deterministic payload for multi-scenario E2E suite generation",
      "prompt": "Use skill new-test-suite-prepare. Ask user for: suite_name, target_domain, and recording_sets[] where each set contains scenario_name, trace_zip_path, checkpoints_json_path, optional metadata_json_path. Do research/planning only (no final code). Before analysis, read AGENTS.md at repo root and all relevant nested AGENTS.md files for target domain/path. Return deterministic mandatory output sections in fixed order, create suite_generation_payload JSON, and save it to thoughts/ai_gen/prepared/ for handoff to /new_test_suite_generate."
    }
  }
}
```

## Register command: /new_test_suite_generate

```json
{
  "command": {
    "new_test_suite_generate": {
      "description": "Generate a coherent multi-scenario E2E suite from prepared suite payload",
      "prompt": "Use skill new-test-suite-generate. Consume suite_generation_payload or suite_generation_payload_path from /new_test_suite_prepare and implement one coherent suite architecture (shared builders/flows, parametrized cases with stable case_id, explicit assertions in tests). Prefer payload file path when provided. Before code changes, read repository guidance in AGENTS.md at repo root and all relevant nested AGENTS.md files for the target domain/path; treat them as mandatory source of truth and list exactly which guides were used. Before implementation, confirm with user: suite name, marker set, severity policy, and file strategy (update existing vs create new). Keep base hosts non-hardcoded, avoid sleeps/retry ladders, and use timeout constants."
    }
  }
}
```

After editing config, restart opencode to load new commands/skills.
