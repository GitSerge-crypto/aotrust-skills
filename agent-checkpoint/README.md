# AOTrust Agent Checkpoint — Notarize Your Work

Give your AI agent a cryptographic "receipt of work" it can show anyone: a
**PDR (Provenance Data Record)** — a signed, 239-byte certificate proving
*what* was produced and *when*. No account, no API key for the free tier.

## What this is for

When an AI agent (or you + an agent) completes critical work — a plan, a patch,
a release, a report — notarize it. You get a **Shield ID** (8 hex chars) that:

- **proves the artifact existed at that moment** (SHA-256 hash + timestamp)
- is **signed** by the notary issuer (Ed25519)
- is **anchored daily to the NEAR blockchain** (publicly auditable)
- is **independently verifiable** by anyone at https://verify.aotrust.link —
  outside your CI, outside your laptop, outside ChatGPT's memory

Think of it as an **external checkpoint** your agent cannot retroactively
falsify. Chat logs can be edited; tickets can be closed; a PDR cannot be
rewritten.

## Quick start (60 seconds)

### Cursor / VS Code MCP clients

Add to `mcp.json` (Cursor: Settings → MCP → Edit Config):

```json
{
  "mcpServers": {
    "aotrust": {
      "url": "https://api.aotrust.link/mcp"
    }
  }
}
```

Or copy [mcp.json](mcp.json) from this directory.

### Cline (VS Code extension)

Settings → MCP Servers → Remote / Import → use
[cline_mcp_settings.json](cline_mcp_settings.json).

### Claude / any MCP client

Point your client at `https://api.aotrust.link/mcp` (streamable HTTP,
free tools work without auth; [AGENT_CHECKPOINT_PROTOCOL.md](AGENT_CHECKPOINT_PROTOCOL.md)
is a copy-paste `AGENTS.md` block that makes the agent notarize critical
checkpoints automatically).

## Available tools

| Tool | What it does | Cost |
|------|--------------|------|
| `notary_quote` | Get a price quote for notarization | free |
| `notary_free` | Notarize without payment (5/day/IP) | **free** |
| `notary_verify` | Verify an existing PDR by job_id | free |
| `notary_notarize` | Notarize via NEAR_DIRECT payment | $0.01 |
| `notary_notarize_paid` | Notarize via x402 USDC on Base | $0.01 |

Start with `notary_free` — no wallet needed.

## Recommended workflow for coding agents

Add this to your `AGENTS.md` (see [AGENTS.md](AGENTS.md) for a copy-paste
version) or paste it into the system prompt:

1. After a **plan is approved** → hash the plan file, `notary_free` it →
   put the Shield ID in the task description.
2. After a **patch is written** (before commit) → hash the diff,
   `notary_free` → reference the Shield ID in the commit message
   (`Provenance: <Shield ID>`).
3. After a **release artifact is built** → use the
   [GitHub Action](https://github.com/marketplace/actions/aotrust-notarize-provenance)
   to notarize `dist/*` automatically.

Anyone can later verify the Shield ID independently — even after the agent
session is closed, the chat is deleted, or the repo is rewritten.

## Verification

```bash
# Verify online (no account needed):
curl https://api.aotrust.link/v1/shield/lookup/<SHIELD_ID>

# Or verify offline with the zero-dependency parser:
python3 pdr_parser.py --pdr <pdr_b64> --format base64
```

## Links

- Free tier: 5 PDRs/day per IP, no account — [docs](https://docs.aotrust.link)
- MCP endpoint: `https://api.aotrust.link/mcp`
- Verify portal: https://verify.aotrust.link
- Python SDK: `pip install aotrust-protocol`
- GitHub Action: [AOTrust Notarize & Provenance](https://github.com/marketplace/actions/aotrust-notarize-provenance)