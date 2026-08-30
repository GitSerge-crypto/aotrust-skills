# AOTrust — Cryptographic Proof of Existence for AI Agents

[![M8ven Score](https://m8ven.ai/badge/mcp/gitserge-crypto-aotrust-skills-g3hz21?v=0f2c915f775a2efe4292a97d389f921c)](https://m8ven.ai/mcp/gitserge-crypto-aotrust-skills-g3hz21)
[![Protected by AOTrust](https://img.shields.io/badge/AOTrust-Notarized-0ea5e9)](https://verify.aotrust.link/s/40aefae4)
![Mainnet Live](https://img.shields.io/badge/mainnet-LIVE-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![PDR v2.3/v2.4](https://img.shields.io/badge/PDR-v2.3%2Fv2.4-blue)
![x402](https://img.shields.io/badge/payment-x402-orange)

AOTrust issues PDRs (Provenance Data Records) — 239-byte cryptographic receipts proving a digital artifact existed at a specific time. $0.01 USDC on Base via x402. Anchored daily to NEAR blockchain. No account needed. Supports ordinary (v0x03) and bilateral (v0x04) signatures.

## Quickstart

```bash
# 1. Compute SHA-256 hash of your artifact
HASH=$(echo -n "Hello AOTrust" | sha256sum | cut -d' ' -f1)

# 2. Request notarization → get 402 payment details
curl -X POST https://api.aotrust.link/notarize \
  -H "Content-Type: application/json" \
  -d "{\"work_hash\":\"$HASH\",\"agent_sig\":\"\",\"agent_pubkey\":\"\"}"

# 3. Pay $0.01 USDC on Base (EIP-3009), then POST with x-payment header
# Full example: see SKILL.md → "Step 3: Pay"
```

For full EIP-3009 signing code (Python + ethers.js examples), see [SKILL.md](aotrust-notarize/SKILL.md).

## Interfaces

| Interface | Best for | Auth |
|-----------|----------|------|
| HTTP API | Developers, scripts, CI/CD | x402 payment (no API key needed) |
| MCP | AI agents (Claude, Cursor) | OAuth 2.1 PKCE |

Endpoints:
- API: `https://api.aotrust.link/notarize`
- MCP: `https://api.aotrust.link/mcp`
- Verify: `https://verify.aotrust.link`
- Docs: `https://docs.aotrust.link`

## PDR Specification & Tools

- [pdr-spec.md](pdr-spec.md) — PDR v2.3/v2.4 binary format (Internal 193B + External 239B, ordinary + bilateral)
- [pdr_parser.py](pdr_parser.py) — standalone parser, zero dependencies, offline verification
- [aotrust-notarize/SKILL.md](aotrust-notarize/SKILL.md) — full integration guide for AI agents

## Comparison

| Feature | AOTrust | Chainlink | OpenTimestamps | Notary.fyi |
|---------|---------|----------|----------------|-----------|
| Price/PDR | $0.01 | $0.25+ | Free (slow) | $0.50+ |
| Payment rail | x402 USDC | LINK | Bitcoin TX | Stripe |
| PDR format | 239B binary | Oracle data | OTS file | PDF |
| AI agent native | MCP + HTTP | No | No | No |
| Blockchain anchor | NEAR (daily) | Ethereum | Bitcoin | None |
| Offline verify | Yes (pdr_parser.py) | No | Yes | No |

## GitHub Action

Notarize build artifacts or AI-generated files directly in CI/CD — free, no wallet needed.

```yaml
- uses: GitSerge-crypto/aotrust-skills@v1.1
  with:
    files: dist/*
```

Outputs: `shield_id`, `verify_url`, `pdr_b64`. Results appear in `$GITHUB_STEP_SUMMARY` as a markdown table with verification links.

### Example workflow

```yaml
name: Release
on:
  release:
    types: [published]

jobs:
  notarize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: GitSerge-crypto/aotrust-skills@v1.1
        with:
          files: dist/*
      - name: Show shield ID
        run: echo "Shield ID: ${{ steps.notarize.outputs.shield_id }}"
```

## License

MIT