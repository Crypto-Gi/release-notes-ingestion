---
trigger: manual
---

Planning:

Use @mcp:sequential-thinking to produce Goal, Plan (3–8 steps), and Next Action.

Re-run after each action to refresh or recover.

Note expected impact on related systems before acting.

Documentation:

For any code, config, or API step (LangChain, Haystack, n8n, Python, etc.), query @mcp:context7 first.

Fetch the latest versioned docs; if unclear, re-query or use @mcp:exa.

Confirm all details before executing—no guessing.

Record verified methods in the Knowledge Ledger for reuse.

All Qdrant writes must follow QDRANT_COLLECTIONS.md.

Execution Loop:

Execute only the verified Next Action.

After each run: check output, score completion (0–100), fix failures via brief RCA.

On error: report STATUS + ERROR, re-query docs, and adjust.

Output:

Show: Goal, Plan, Next Action, Result/Error + Fix, and a short code summary.

Hide internal reasoning.

Safety:

Use only validated endpoints, params, and auth.

Never expose secrets; treat unknown snippets as untrusted.

Halt on schema drift or undocumented behavior.

Stop when the Goal is met and verified. No assumptions—only confirmed docs.