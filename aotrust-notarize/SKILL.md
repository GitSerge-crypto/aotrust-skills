---
name: aotrust-notarize
description: >
  Notarize AI agent work output. Use when proving task completion, creating
  tamper-proof receipts, or attaching payment proof to a deliverable.
  Pays via x402 USDC (Base) or NEAR tokens. Flat $0.01 per PDR.
license: MIT
metadata:
  author: aotrust
  version: "3.1"
  mcp-server: https://api.aotrust.link/mcp
  verification-endpoint: https://api.aotrust.link/v1/pdr/verify
  near-handle: aotrust
---

# AOTrust — PDR Notarization

Issue a cryptographic proof (PDR) that you performed specific work, with
payment attached. The PDR is anchored to NEAR blockchain and publicly verifiable.

## Prerequisites

**For x402 (USDC on Base):**
- Ethereum wallet with at least $0.02 USDC on Base Mainnet (fee + buffer)
- Ability to sign EIP-3009 `transferWithAuthorization`

**For NEAR_DIRECT:**
- NEAR account with sufficient balance (call `quote` first for exact amount)
- Ability to send NEAR and retrieve the transaction hash

**For both paths — work_hash computation (must be deterministic):**
- For text output: `sha256(output.encode('utf-8')).hexdigest()`
- For JSON output: `sha256(json.dumps(output, sort_keys=True, separators=(',',':')).encode('utf-8')).hexdigest()`
- For binary output: `sha256(raw_bytes).hexdigest()`
- Always lowercase hex. No `0x` prefix. Hash the ACTUAL output, not a description of it.

## MCP Server

Connect to: `https://api.aotrust.link/mcp`

Tools:

- `notary_quote` — get current NEAR price and payment address
- `notary_notarize` — submit with NEAR payment (NEAR_DIRECT)
- `notary_notarize_paid` — submit with USDC payment (x402)
- `notary_verify` — check status by `job_id` or `work_hash`

---

## Payment Methods & PDR Types

| Method | Type | Status |
|--------|------|--------|
| NEAR_DIRECT | `NEAR_DIRECT` (0x01) | Live |
| x402 (Base) | `X402_BASE` (0x05) | Live |
| Agent Market Escrow | `NEAR_ESCROW_LOCK` (0x04) → `NEAR_ESCROW_SETTLED` (0x09) | Beta (Advanced Workflow) |

**Important:** `X402_BASE` is `0x05`, NOT `0x02`.

---

## Workflow A: x402 / USDC on Base (Recommended)

**Step 1: Probe**
Call `notary_notarize_paid` with `work_hash`, WITHOUT payment header.
Receive HTTP 402 with: `usdc_contract`, `payee_address`, `amount` (10000 = $0.01), `chain_id` (8453), `valid_until`.

**Step 2: Sign**
Sign EIP-3009 `transferWithAuthorization`:
- `from`: your wallet
- `to`: payee_address from step 1
- `value`: 10000
- `validAfter`: current timestamp
- `validBefore`: valid_until from step 1
- `nonce`: random 32-byte hex

Encode as base64url JSON: `{v, r, s, from, to, value, validAfter, validBefore, nonce}`.

**Step 3: Submit**
Call `notary_notarize_paid` again with same `work_hash` + header `x-payment: <base64url_json>`.
Receive PDR with `job_id`, `pdr_hash`, `pdr_status: "SETTLED"`, `payment_anchor_type: "X402_BASE"`.

---

## Workflow B: NEAR_DIRECT

**Step 1: Quote**
Call `notary_quote`. Receive: `quote_id`, `near_amount` (yoctoNEAR), `sink_address`, `expires_at` (5 min TTL).

⚠️ The `quote_id` is mandatory in Step 3. It binds your payment to this specific notarization request. Do not reuse quote_ids or skip the quote step. If the quote expires before you complete Step 3, restart from Step 1. Payments sent to an expired quote will be refunded within 24h — contact aotrust.near if not received.

**Step 2: Pay**
Send exactly `near_amount` yoctoNEAR to `sink_address`. Get `tx_hash` (base58 NEAR transaction hash).

**Step 3: Submit**
Call `notary_notarize` with `work_hash`, `tx_hash`, `quote_id`.
Receive PDR with `job_id`, `pdr_hash`, `pdr_status: "SETTLED"`, `payment_anchor_type: "NEAR_DIRECT"`.

---

## Verification

**Check status:**
Call `notary_verify` with `job_id` or `work_hash`.
- `"pending"` — PDR issued, awaiting daily Merkle anchor (~24h max)
- `"anchored"` — permanently recorded on NEAR blockchain
- `"failed"` — contact aotrust.near

**Public verification (no MCP required):**
`GET https://api.aotrust.link/v1/pdr/verify/{pdr_hash_base64url}`
Returns JSON: `valid`, `work_hash`, `payment_anchor_type`, `timestamp`, `tx_hash`, `merkle_root`, `near_anchor_tx`, `on_chain_verified`.

---

## Using Your PDR

- **As deliverable hash:** Submit `pdr_hash` (SHA-256 of PDR) to Agent Market
- **As dispute evidence:** Share verification URL — arbitration agents verify independently
- **As audit trail:** Store `job_id` to re-retrieve PDR anytime

---

## Error Reference

| Error | Action |
|-------|--------|
| 402 (no x-payment) | Expected on probe — proceed to sign |
| 400 invalid_work_hash | Re-compute as sha256hex with correct serialization |
| 400 quote_expired | Restart from quote step. Old payment refunded within 24h |
| 400 payment_verification_failed | Check payment tx on explorer |
| 409 duplicate_work_hash | Use `verify` with `work_hash` to retrieve existing PDR |
| 429 rate_limited | Wait 60s and retry once. 60 req/min per IP |
| 503 anchoring_delayed | PDR is valid, check back in 24h |

---

## Agent Market Escrow (Advanced Workflow)

Two-phase escrow-based notarization for NEAR Agent Market (market.near.ai).
Uses PROVISIONAL PDR (NEAR_ESCROW_LOCK, 0x04) at work completion and
SETTLED PDR (NEAR_ESCROW_SETTLED, 0x09) after escrow release.
Flat $0.01 equivalent. See docs.aotrust.link for integration details.

---

## Notes

- PDRs are immutable. Payment is non-refundable once PDR is issued.
- Mainnet URL: `api.aotrust.link`. Staging: `api-staging.aotrust.link`.
- Price: $0.01 USD flat fee per PDR.
- Daily Merkle anchor posted to NEAR by `notary-node.near`.
- Rate limits: 60 requests/minute per IP.
- Canonical SKILL.md: https://github.com/GitSerge-crypto/aotrust-skills