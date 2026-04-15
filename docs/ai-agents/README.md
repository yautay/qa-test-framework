# AI Agents Guide

This directory contains guidelines for AI agents that generate automated tests.

## Scope

- Priority: **E2E** (`qa/e2e/`).
- Goal: generate tests from a test environment URL and scenario prompt.
- Requirement: preserve current code style and existing POM architecture.

## What these guidelines cover

- How to inspect code before generating a test.
- How to build POM using the `page.section.component.method` pattern.
- How to avoid unnecessary Page Objects.
- How to preserve pytest markers, style, and fixture usage.

## Quick Start (E2E)

1. Read `docs/ai-agents/e2e/AGENT_MANIFEST.md`.
2. Read `docs/ai-agents/e2e/POM_CONTRACT.md`.
3. Follow `docs/ai-agents/e2e/TEST_GENERATION_FLOW.md`.
4. Complete `docs/ai-agents/e2e/CHECKLIST.md`.

## E2E Directory

- `docs/ai-agents/e2e/AGENT_MANIFEST.md`
- `docs/ai-agents/e2e/POM_CONTRACT.md`
- `docs/ai-agents/e2e/TEST_GENERATION_FLOW.md`
- `docs/ai-agents/e2e/SELECTOR_AND_ASSERTION_RULES.md`
- `docs/ai-agents/e2e/JOB_WORKSPACE.md`
- `docs/ai-agents/e2e/PROMPT_TEMPLATE.md`
- `docs/ai-agents/e2e/CHECKLIST.md`

## OpenCode Integration

- Registerable OpenCode commands live in `tools/opencode/commands/`.
- Setup and registration instructions: `tools/opencode/README.md`.
- Versioned E2E job workspace: `work/e2e-jobs/`.
