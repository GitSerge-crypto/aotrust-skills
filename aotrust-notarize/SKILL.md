---
name: aotrust-notarize
description: >
  Issue a cryptographic proof (PDR) that a digital artifact existed at a specific time.
  Pay $0.01 USDC on Base via x402. Anchored daily to NEAR blockchain. Publicly verifiable.
license: MIT
metadata:
  author: aotrust
  version: "3.3"
  verification-endpoint: https://api.aotrust.link/v1/pdr/verify
  near-handle: aotrust
---

# AOTrust — Get a PDR in 3 Steps

A PDR (Provenance Data Record) is a 239-byte cryptographic receipt proving
a digital artifact existed at a specific point in time. Anchored daily to
NEAR blockchain. $0.01 per proof. No account needed.

## What You Need

- An Ethereum wallet on **Base Mainnet** with:
  - At least **$0.01 in USDC** (for the PDR fee)
  - A small amount of **ETH** (for gas, typically less than $0.01)
- Ability to make HTTP requests and sign EIP-3009 `transferWithAuthorization`

## How It Works

```
YOUR AGENT → POST work_hash to /notarize
           ← HTTP 402 with payment details (payTo, amount, network)
YOUR AGENT → sign EIP-3009 with your Ethereum key
YOUR AGENT → POST work_hash + x-payment header
           ← HTTP 200 with PDR (239 bytes, base64)
```

---

## Step-by-Step

### Step 1: Compute the Work Hash

Hash your artifact with SHA-256. This is what gets notarized — not the artifact itself.

```python
import hashlib
work_hash = hashlib.sha256(b"your digital artifact content").hexdigest()
```

### Step 2: Request Notarization (No Payment Yet)

Send your work_hash. The server responds with payment instructions.

```bash
curl -X POST https://api.aotrust.link/notarize \
  -H "Content-Type: application/json" \
  -d '{"work_hash":"YOUR_SHA256_HEX"}'
```

**Response (HTTP 402):**
```json
{
  "payTo": "0x97E9af6B4d8a49f509DA99afaB954429Ab8Cc800",
  "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "maxAmountRequired": "10000",
  "network": "eip155:8453",
  "maxTimeoutSeconds": 300
}
```

- `payTo` — where to send payment
- `asset` — USDC contract on Base
- `maxAmountRequired` — 10000 micro-USDC = $0.01
- `network` — Base Mainnet (chain ID 8453)

### Step 3: Pay and Get Your PDR

Sign an EIP-3009 `transferWithAuthorization` with your Ethereum key:

- `from`: your wallet address
- `to`: the `payTo` address from Step 2
- `value`: `maxAmountRequired` from Step 2 (10000 = $0.01)
- `validAfter`: current Unix timestamp
- `validBefore`: current time + `maxTimeoutSeconds`
- `nonce`: random 32-byte hex string

Encode the signature as base64url JSON. Then send it with the `x-payment` header:

```bash
curl -X POST https://api.aotrust.link/notarize \
  -H "Content-Type: application/json" \
  -H "x-payment: YOUR_BASE64URL_ENCODED_SIGNATURE" \
  -d '{"work_hash":"YOUR_SHA256_HEX"}'
```

**Response (HTTP 200):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "pdr_b64": "AwEFA1kuagAAAABub3...",
  "tx_hash": "0x3c7133009a74...",
  "payment_anchor_type": "X402_BASE"
}
```

Done. `pdr_b64` is your 239-byte cryptographic proof.

---

## Verify Your PDR

Go to `https://verify.aotrust.link` and enter the `job_id`.

Or verify programmatically:
```bash
curl https://api.aotrust.link/v1/pdr/verify/YOUR_PDR_B64
```

Anyone can verify — no account, no key, no authentication required.

---

## What a PDR Proves

- ✅ Your artifact (identified by its SHA-256 hash) existed at a specific time
- ✅ Payment was settled on Base Mainnet (tx_hash verifiable on-chain)
- ✅ The notary (notary-node.near) signed the record
- ✅ The record is anchored to NEAR blockchain via daily Merkle root

A PDR does NOT reveal your artifact content — only its hash.

---

## Error Reference

| Response | Meaning | Action |
|----------|---------|--------|
| HTTP 402 | Expected — payment required | Proceed to step 3 |
| HTTP 400 | Invalid work_hash format | Must be 64-char lowercase hex |
| HTTP 409 | Duplicate work_hash | Already notarized — use verify |
| HTTP 429 | Rate limited | Wait 60 seconds, retry once |

---

## Notes

- Price: **$0.01 USDC** flat per PDR. No tiers, no subscriptions.
- PDRs are **immutable**. Once issued, they cannot be modified.
- Payment is **non-refundable** after PDR issuance.
- Daily Merkle root anchored to NEAR by `notary-node.near`.
- Rate limit: 60 requests/minute per IP.
- Canonical SKILL.md: https://github.com/GitSerge-crypto/aotrust-skills