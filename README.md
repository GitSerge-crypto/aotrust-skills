# AOTrust — Cryptographic Proof of Existence for AI Agents

[![M8ven Score](https://m8ven.ai/badge/mcp/gitserge-crypto-aotrust-skills-g3hz21?v=0f2c915f775a2efe4292a97d389f921c)](https://m8ven.ai/mcp/gitserge-crypto-aotrust-skills-g3hz21)
[![Protected by AOTrust](https://img.shields.io/badge/AOTrust-Notarized-0ea5e9)](https://verify.aotrust.link/s/40aefae4)
![Mainnet Live](https://img.shields.io/badge/mainnet-LIVE-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![PDR v2.3/v2.4](https://img.shields.io/badge/PDR-v2.3%2Fv2.4-blue)
![x402](https://img.shields.io/badge/payment-x402-orange)

AOTrust issues PDRs (Provenance Data Records) — 239-byte cryptographic receipts proving a digital artifact existed at a specific time. $0.01 USDC on Base via x402. Anchored daily to NEAR blockchain. No account needed. Supports ordinary (v0x03) and bilateral (v0x04) signatures.

**Positioning: an Independent External Provenance Checkpoint.** Native
attestations (Sigstore, GitHub artifact attestations) verify a build *inside*
the CI system that produced it. AOTrust complements them: it issues a signed
certificate *outside* GitHub/Microsoft infrastructure and anchors it daily to
the NEAR blockchain — so provenance survives even if the repository is
rewritten, the CI logs disappear, or the attestation store is unavailable.
Use both.

## Agent Checkpoint (new)

Connect your AI coding agent in 60 seconds and make it notarize
plan/patch/release checkpoints — free tier, no account:
**[agent-checkpoint/](agent-checkpoint/)** — mcp.json drop-ins for Cursor,
Cline, and any MCP client, plus a copy-paste `AGENTS.md` block
(`Provenance: <Shield ID>` in commits).

## Authorship Claims (bilateral signatures)

Beyond agent workflows, AOTrust supports **bilateral PDRs (v0x04)**: the
artifact is signed by **you** (Ed25519) *and* countersigned by the notary —
a binding hash ties your public key to the content. This turns "I wrote/published
this first" into a verifiable claim for **any digital artifact**: manuscripts,
designs, photos, research notes, legal correspondence. Verification is public
at https://verify.aotrust.link — no account, no software install for the reader.
Signing guide (Ed25519, NEP-413): [SKILL.md → Bilateral Signature](aotrust-notarize/SKILL.md#bilateral-signature-optional-v0x04).
See [pdr-spec.md](pdr-spec.md) §v2.4 for the binding-hash construction.

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
| HTTP API | Developers, scripts, CI/CD | x402 payment (no API key needed); free tier 5/day/IP |
| MCP | AI agents (Claude, Cursor, Cline) | None for discovery + free tools (notary_free 5/day/IP) |

Endpoints:
- API: `https://api.aotrust.link/notarize`
- MCP: `https://api.aotrust.link/mcp`
- Verify: `https://verify.aotrust.link`
- Docs: `https://docs.aotrust.link`

## Verify API (public, embeddable)

Verification is a **standalone public API** — no account, no rate limits, no
payment. Embed it in your product (dashboards, audit tools, escrow flows)
or call it from the terminal:

```bash
# Verify a PDR (base64url-encoded bundle):
curl https://api.aotrust.link/v1/pdr/verify/<pdr_b64url>
# → {"valid": true, "checks": {...}, "error": null}

# Look up a PDR by Shield ID (8 hex chars):
curl https://api.aotrust.link/v1/shield/lookup/<shield_id>
# → {"found": true, "pdr_b64": "...", "shield_id": "..."}

# Get the notary public key for offline verification:
curl https://api.aotrust.link/v1/notary/pubkey
```

Prefer full offline trust? [pdr_parser.py](pdr_parser.py) verifies any PDR
locally — zero dependencies, no network, no trust in our servers.

### Offline Merkle verification (anchored receipts)

Anchored PDRs carry the daily Merkle root committed on-chain in the NEAR
contract `notary-node.near` — readable from **any public NEAR RPC**, forever,
independent of our servers. The verify API returns `merkle_proof`,
`merkle_index`, `merkle_leaf` and `merkle_tree_size` for anchored PDRs.
**Save the verify JSON response** — then verify it forever, offline:

```bash
# (once) save the verify response when the receipt is fresh:
curl https://api.aotrust.link/v1/pdr/verify/<pdr_b64url> > verify.json

# (any time, no AOTrust server needed) check inclusion:
python3 verify_merkle_inclusion.py \
  --leaf <merkle_leaf> --proof <comma-joined merkle_proof> \
  --index <merkle_index> --root <merkle_root> \
  --tree-size <merkle_tree_size>
# → VALID

# the root can always be re-checked against the chain itself via any
# NEAR RPC: contract notary-node.near, method get_root({"seq": N})
```

[verify_merkle_inclusion.py](verify_merkle_inclusion.py) is standalone and
zero-dependency (RFC 9162 §2.1.3.2 walk, same hashing as the anchoring
engine). `tree_size` must be taken from the verify response (or a published
anchor snapshot), not chosen by the verifier.

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