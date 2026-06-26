# AOTrust — Cryptographic Proof of Existence for AI Agents

![Mainnet Live](https://img.shields.io/badge/mainnet-LIVE-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![PDR v2.3](https://img.shields.io/badge/PDR-v2.3-blue)
![x402](https://img.shields.io/badge/payment-x402-orange)

AOTrust issues PDRs (Provenance Data Records) — 239-byte cryptographic receipts proving a digital artifact existed at a specific time. $0.01 USDC on Base via x402. Anchored daily to NEAR blockchain. No account needed.

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

- [pdr-spec.md](pdr-spec.md) — PDR v2.3 binary format (Internal 193B + External 239B)
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

## License

MIT