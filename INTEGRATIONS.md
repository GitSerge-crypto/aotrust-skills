# AOTrust MCP — Integrations

Connect the AOTrust MCP server to your coding assistant in under a minute.
No account, no API key — start with the **free tier** (5 receipts/day per IP).

**MCP server URL:** `https://api.aotrust.link/mcp` (Streamable HTTP; legacy `https://api.aotrust.link/sse` also available)

**What you get:** 5 tools — `notary_free`, `notary_quote`, `notary_notarize`, `notary_notarize_paid`, `notary_verify` — cryptographic receipts (Ed25519 PDR) for any artifact, anchored daily to the NEAR blockchain.

---

## Cursor

Create `.cursor/mcp.json` in your project (or `~/.cursor/mcp.json` for all projects):

```json
{
  "mcpServers": {
    "aotrust": {
      "url": "https://api.aotrust.link/mcp"
    }
  }
}
```

Restart Cursor → **Customize** → the `aotrust` server should show as enabled with 5 tools.

## Windsurf / Cline / any MCP client with remote servers

Same shape as Cursor — a `mcpServers` block with the server URL:

```json
{
  "mcpServers": {
    "aotrust": {
      "url": "https://api.aotrust.link/mcp"
    }
  }
}
```

Legacy SSE transport (if your client predates Streamable HTTP): use
`https://api.aotrust.link/sse` as the URL.

## Claude Desktop

Claude Desktop's config file only accepts local (stdio) servers, so use one of:

**Option A — Connectors UI (preferred):** open **Settings → Connectors → Add
connector**, enter `https://api.aotrust.link/mcp`.

**Option B — mcp-remote bridge:** edit `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`,
Windows: `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "aotrust": {
      "command": "npx",
      "args": ["mcp-remote", "https://api.aotrust.link/mcp"]
    }
  }
}
```

Requires Node.js (npx). Restart Claude Desktop after editing.

## 30 seconds — your first receipt (no keys)

Once the server is connected, ask your assistant:

> Use `notary_free` to notarize the phrase "hello world" — first compute its SHA-256.

Or from any terminal:

```bash
python3 -c "import hashlib; print(hashlib.sha256(b'hello world').hexdigest())"
# → pass the 64-char hash to notary_free as work_hash
```

The response contains `shield_id` (8 hex), the 239-byte PDR, and a
`verify_url`. Verify it anytime at `https://verify.aotrust.link/?pdr=<pdr_b64>`.

## Make your assistant notarize commits automatically

Drop this rule into your project (`.cursorrules`, `CLAUDE.md`, or your assistant's
rules file) — every completed task then produces a cryptographic receipt:

```markdown
## Provenance rule (AOTrust)

Before finishing a non-trivial task or handing off a critical file:
1. Compute SHA-256 of the final artifact (file content or diff text).
2. Call the `notary_free` tool with the 64-hex hash as work_hash.
3. Include the returned shield_id and verify_url in your summary.
If the free-tier limit (5/day) is reached, state it and continue without a receipt.
```

The receipt proves the artifact existed at that moment, signed by the notary
(`notary-node.near`) and anchored daily to NEAR — independently verifiable forever.

## Verify receipts — even offline

- **Instant:** `https://verify.aotrust.link/?pdr=<pdr_b64>` or
  `GET https://api.aotrust.link/v1/pdr/verify/<pdr_b64>`
- **Python:** `pip install aotrust-protocol` →
  [`pdr_parser.py`](pdr_parser.py) verifies any PDR locally (zero deps).
- **Forever:** the verify response carries `merkle_proof`, `merkle_index`,
  `merkle_leaf`, `merkle_tree_size`, `merkle_root` — save it, and
  [`verify_merkle_inclusion.py`](verify_merkle_inclusion.py) (RFC 9162)
  re-verifies inclusion against the on-chain root from any public NEAR RPC.
  No AOTrust server needed.

## Paid path (flat $0.01)

Free tier is rate-limited (5/day per IP). For volume: `notary_quote` → pay →
`notary_notarize_paid`, or HTTP `x402` flow per
[`aotrust-notarize/SKILL.md`](aotrust-notarize/SKILL.md). Flat $0.01 USDC on Base
per PDR — see the [.well-known/x402 manifest](https://api.aotrust.link/.well-known/x402).

## Python SDK examples

`aotrust-protocol` (PyPI) — asyncio client:

```python
import asyncio, hashlib
from agent_notary import NotaryClient

async def main():
    client = NotaryClient(base_url="https://api.aotrust.link/v1")
    work_hash = hashlib.sha256(b"my artifact").hexdigest()
    res = await client.shield_free(work_hash)   # free tier, no key
    print(res["shield_id"], res["verify_url"])

asyncio.run(main())
```

Framework wrappers live in [`examples/`](https://github.com/GitSerge-crypto/aotrust-skills/tree/main/examples)
(LangChain `BaseTool`, CrewAI custom Tool) — small, copy-paste, no framework lock-in.

---

*Server status: `GET https://api.aotrust.link/health`. Spec:
[pdr-spec.md](pdr-spec.md). Full agent guide:
[aotrust-notarize/SKILL.md](aotrust-notarize/SKILL.md).*