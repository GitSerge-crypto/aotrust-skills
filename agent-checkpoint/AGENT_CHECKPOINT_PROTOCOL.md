# Agent Checkpoint Protocol — AGENTS.md integration

Copy the block below into your project's `AGENTS.md` (or your agent's system
prompt / memory) to make the agent notarize critical checkpoints automatically.
This file itself is a template to copy FROM — dropping it into a repo as
`AGENTS.md` makes its rules part of that repo's agent instructions.

---

```markdown
## Agent Checkpoint Protocol (AOTrust)

You are connected to the AOTrust notarization service (MCP server:
https://api.aotrust.link/mcp). Use it to create tamper-proof, externally
verifiable checkpoints of your work.

WHEN TO NOTARIZE (use the free `notary_free` tool; it needs only a SHA-256
hex digest and costs nothing, limit 5/day):

1. After a plan or architecture decision is FINAL (before implementation):
   hash the plan document, notarize it, report the 8-char Shield ID.

2. Before every commit that implements a user-requested feature or fix:
   hash the final diff (git diff | sha256sum), notarize it, and include the
   Shield ID in the commit message on a line:  Provenance: <Shield ID>

3. At handoff (end of session / task completion):
   hash the summary of what was done, notarize it, include the Shield ID
   in your final report to the user.

HOW:

- work_hash = sha256 of the artifact content (hex, 64 chars)
- call notary_free with {"work_hash": "<64hex>"}
- report the returned Shield ID (8 hex chars) and verify URL
  https://verify.aotrust.link/s/<SHIELD_ID>

RULES:

- Never fabricate or pre-compute a Shield ID — always call the tool.
- One notarization per meaningful artifact (do not spam the free quota).
- If the free quota is exhausted, skip silently and note it — do not pay.
- When verification is questioned, offer the verify URL; anyone can check it
  without an account.
```

---

## Why this matters

- **For maintainers receiving agent PRs:** a `Provenance:` line proves the
  patch existed (in this exact form) at a specific time, anchored to a public
  blockchain — it was not silently regenerated after review comments.
- **For agent operators:** prove your agent did the job it claims, without
  exposing your chat logs.
- **For auditors:** every checkpoint is independently verifiable offline with
  [pdr_parser.py](https://github.com/GitSerge-crypto/aotrust-skills) — no
  trust in our servers required.

## Example commit

```
fix: prevent race in cache invalidation

...
Provenance: 4a1b2c3d (https://verify.aotrust.link/s/4a1b2c3d)
```
