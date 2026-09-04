# Security Policy

## Reporting a Vulnerability

**Contact:** legal@aotrust.link (preferred, monitored) or open a private GitHub
security advisory on this repository.

**Response commitment:** acknowledgment within 72 hours; honest timeline for a fix
if the report is accepted; credit in this file and release notes if you want it.

**Scope — in:** the PDR binary spec (`pdr-spec.md`), the offline verifier
(`pdr_parser.py`), the Python SDK (`aotrust-protocol` on PyPI), the GitHub Action
(`action/`), MCP drop-ins (`agent-checkpoint/`), and the public API surface
(api.aotrust.link, verify.aotrust.link, shield.aotrust.link).

**Out of scope:** social engineering of the operator, denial-of-service by volume
(rate limits handle this), attacks on third parties (Base, NEAR, x402 facilitator
payai.network) that don't go through our code, phishing of our users.

## Trust Model — what a PDR proves, and what it deliberately does not

**You do NOT need to trust AOTrust to verify a receipt.** Three independent layers:

1. **Open binary spec** (`pdr-spec.md`) — exact byte layout, offsets, NEP-413
   signing construction, Binding Hash formula for bilateral (v0x04) receipts.
2. **Offline verifier** (`pdr_parser.py`) — parse and check any receipt locally,
   no network, no API call. Signature check uses the notary public key.
3. **NEAR anchor** — receipts are anchored daily to mainnet account
   `notary-node.near`. Anyone can independently confirm the anchor via NEAR RPC.

What a PDR proves: that a specific 32-byte `work_hash` was notarized at a specific
time by the notary key (and, for v0x04, bound to a client Ed25519 signature +
agent pubkey).

What a PDR deliberately does NOT prove: who authored the underlying artifact, that
its contents are truthful, that the notarizing party is the artifact's owner. A
receipt is evidence of existence and binding, not a verdict on quality or identity.

## Threat Model (summary)

- **Server compromise** (notary server closed-source): the notary key could sign
  fake receipts. Mitigation: anchors are public and auditable on NEAR; the same
  notary key anchors a verifiable daily history — back-dating an artifact after
  discovery requires forging anchor history, which the chain exposes. Residual
  trust: the notary key itself (single key, VPS-held).
- **Facilitator compromise** (x402, payai): a dishonest facilitator could report
  a settle that didn't happen. Mitigation: PDR issuance happens only after
  `settle.success=True` (Server-SR1, verified against USENIX 2607.19545 rules);
  payment ledger is reconciled against on-chain Base data during audits.
- **Client-side**: the SDK never asks for private keys or seed phrases; x402
  payment is signed client-side via EIP-3009 with the payer's own wallet.
- **Denial of service**: rate limits on free/CI tiers (per-IP, per-key, global
  daily hardcap). Verify endpoints are unauthenticated by design — a PDR must be
  verifiable without an account.
- **Known residual risks** (documented in
  `research/design_notes/2026-08-31-x402-security-rules-vs-ingress.md` in the
  private repo): R-1 verify-call DoS cost (mitigated by rate limits), R-2
  facilitator false-settle (trust boundary of the protocol, monitored on-chain).

## Safe-Use Guarantee (skills and MCP server)

AOTrust skills and MCP server will NEVER:
- Request your private key, seed phrase, or wallet password
- Execute shell commands or install software
- Access files outside the notarization workflow

## Verification

All PDR receipts are verifiable at:
https://verify.aotrust.link/?pdr={base64url} — or fully offline with
`pdr_parser.py` (see spec for the byte layout).

Source code: https://github.com/GitSerge-crypto/aotrust-skills