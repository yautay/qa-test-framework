# Analyze DOM and refine scenario

Input:

- SERVER_NAME: $SERVER_NAME
- PAGE_PATH: $PAGE_PATH
- SCENARIO_PROMPT: $SCENARIO_PROMPT

Task:

1. Capture and cache DOM once:
   - `python tools/opencode/cache_dom_snapshot.py --server-name=$SERVER_NAME --path=$PAGE_PATH`
2. Read cached artifacts from the printed `latest` directory:
   - `dom_digest.md`
   - `summary.json`
   - `page.html`
   - `page.png`
3. Analyze DOM against `SCENARIO_PROMPT` and detect unclear business behavior.
4. Ask the user 3-7 focused follow-up questions about expected behavior.
5. Produce a refined scenario contract and save it next to cached DOM as:
   - `refined_behavior_contract.md`

Output format:

- Section `Observed UI` (what is present in DOM and relevant selectors),
- Section `Open Questions` (targeted behavior questions),
- Section `Refined Scenario Draft` (ready for implementation),
- Path to saved contract file.

Rules:

- Keep this command analysis-only (no test implementation yet).
- Keep focus on E2E behavior.
- Prefer stable selectors (`data-*`) in findings.
