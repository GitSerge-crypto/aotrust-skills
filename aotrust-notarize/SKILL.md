---
name: aotrust-notarize
description: >
  Notarize AI agent work output. Use when proving task completion, creating
  tamper-proof receipts, or attaching payment proof to a deliverable.
  Pays via USDC on Base (x402) or NEAR tokens.
license: MIT
metadata:
  author: aotrust
  version: "2.3"
  mcp-server: https://api-staging.aotrust.link/mcp
  verification-endpoint: https://api-staging.aotrust.link/v1/pdr/verify
  near-handle: aotrust
---

# A&O Trust Layer — Notarization

Issue a cryptographic proof (PDR/VET) that you performed specific work, with
payment attached. The PDR is anchored to NEAR blockchain and publicly verifiable.

## Prerequisites

**For x402 (USDC on Base):**
- Ethereum wallet with at least $0.06 USDC on Base Mainnet (fee + buffer)
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

Connect to: `https://api-staging.aotrust.link/mcp`

Tools (all prefixed `agent_notary_`):

> Note: Tool names follow the pattern `agent_notary_notary_{action}`. The
> double `notary_notary` is correct — MCP server prefix + tool group.
> Copy tool names exactly as shown.

- `agent_notary_notary_quote` — get current NEAR price and payment address
- `agent_notary_notary_notarize` — submit with NEAR payment (NEAR_DIRECT)
- `agent_notary_notary_notarize_paid` — submit with USDC payment (x402)
- `agent_notary_notary_verify` — check status by `job_id` or `work_hash`

---

## Workflow A: x402 / USDC on Base (Recommended)

**Step 1: Probe**
Call `agent_notary_notary_notarize_paid` with `work_hash`, WITHOUT payment header.
Receive HTTP 402 with: `usdc_contract`, `payee_address`, `amount` (50000 = $0.05), `chain_id` (8453), `valid_until`.

**Step 2: Sign**
Sign EIP-3009 `transferWithAuthorization`:
- `from`: your wallet
- `to`: payee_address from step 1
- `value`: 50000
- `validAfter`: current timestamp
- `validBefore`: valid_until from step 1
- `nonce`: random 32-byte hex

Encode as base64url JSON: `{v, r, s, from, to, value, validAfter, validBefore, nonce}`.

**Step 3: Submit**
Call `agent_notary_notary_notarize_paid` again with same `work_hash` + header `x-payment: <base64url_json>`.
Receive PDR with `job_id`, `pdr_hash`, `pdr_status: "SETTLED"`, `payment_anchor_type: "X402_BASE"`.

---

## Workflow B: NEAR_DIRECT

**Step 1: Quote**
Call `agent_notary_notary_quote`. Receive: `quote_id`, `near_amount` (yoctoNEAR), `sink_address`, `expires_at` (5 min TTL).

⚠️ The `quote_id` is mandatory in Step 3. It binds your payment to this specific notarization request. Do not reuse quote_ids or skip the quote step. If the quote expires before you complete Step 3, restart from Step 1. Payments sent to an expired quote will be refunded within 24h — contact aotrust.near if not received.

**Step 2: Pay**
Send exactly `near_amount` yoctoNEAR to `sink_address`. Get `tx_hash` (base58 NEAR transaction hash).

**Step 3: Submit**
Call `agent_notary_notary_notarize` with `work_hash`, `tx_hash`, `quote_id`.
Receive PDR with `job_id`, `pdr_hash`, `pdr_status: "SETTLED"`, `payment_anchor_type: "NEAR_DIRECT"`.

---

## Verification

**Check status:**
Call `agent_notary_notary_verify` with `job_id` or `work_hash`.
- `"pending"` — PDR issued, awaiting daily Merkle anchor (~24h max)
- `"anchored"` — permanently recorded on NEAR blockchain
- `"failed"` — contact aotrust.near

**Public verification (no MCP required):**
`GET https://api-staging.aotrust.link/v1/pdr/verify/{pdr_hash_base64url}`
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

## Agent Market Escrow (Beta)

For NEAR Agent Market jobs: `NEAR_ESCROW_LOCK` (0x04) → `NEAR_ESCROW_SETTLED` (0x09).
Two-phase PDR for escrow-based payments.

**To test:** Post a job on market.near.ai with `service_id: f92dc109-...`, budget $0.05 NEAR, `deliverable_type: hash`. aotrust responds with PROVISIONAL PDR. Accept the deliverable to trigger SETTLED PDR upgrade. Contact aotrust.near on NEAR AI Discord with job_id to coordinate.

---

## Notes

- PDRs are immutable. Payment is non-refundable once PDR is issued.
- Staging URL: `api-staging.aotrust.link`. Update to `api.aotrust.link` after mainnet launch.
- Price: $0.05 USD equivalent on all payment rails.
- Daily Merkle anchor posted to NEAR by `notary-node.near`.
- Rate limits: 60 requests/minute per IP.
