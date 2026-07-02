# PDR Format Specification (v2.3 + v2.4 Bilateral)

<!-- Based on STATE_OF_TRUTH v8.6 (2026-07-02). Regenerate when PDR version changes. -->

Provenance Data Record (PDR) — the cryptographically signed artifact issued by AOTrust.

## Overview

A PDR is a fixed-size binary record that proves an AI agent produced specific work at a specific time. Two formats exist:

| Format | Size | Use |
|---|---|---|
| Internal | 193 bytes | Notary-internal storage, never exposed to clients |
| External | 239 bytes | Client-facing, self-verifying artifact |

All client-facing PDRs are External (239 bytes). Internal PDRs are an implementation detail of the notary service.

---

## External PDR (239 bytes)

```
Format: <BBBQ36s32s32s32s32s64s
Total:  1 + 1 + 1 + 8 + 36 + 32 + 32 + 32 + 32 + 64 = 239 bytes
```

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 1 | `version` | U8 | PDR version: `0x03` (ordinary) or `0x04` (bilateral) |
| 1 | 1 | `sig_scheme` | U8 | Signature scheme: `0x01` = Ed25519 |
| 2 | 1 | `payment_anchor_type` | U8 | Payment rail enum (see below) |
| 3 | 8 | `timestamp_utc` | U64 | Unix timestamp in seconds |
| 11 | 36 | `issuer_id` | bytes(36) | Notary NEAR account, NUL-padded (e.g. `notary-node.near`) |
| 47 | 32 | `subject_hash` | bytes(32) | SHA-256 of agent account |
| 79 | 32 | `payload_hash` | bytes(32) | v0x03: SHA-256 of work result. v0x04: Binding Hash = `sha256(work_hash + sig_A + agent_pubkey)` |
| 111 | 32 | `merkle_root` | bytes(32) | Merkle root from daily on-chain anchor |
| 143 | 32 | `payment_hash` | bytes(32) | Payment transaction hash (multi-chain) |
| 175 | 64 | `signature` | bytes(64) | Ed25519 signature (NEP-413) |

**Payload** = bytes 0–174 (175 bytes). **Signature** = bytes 175–238 (64 bytes).

### Signature Scheme

The Ed25519 signature follows [NEP-413](https://github.com/near/NEPs/blob/master/neps/nep-413.md):

```
NEP413_buffer = pack("<II175s", 2147484061, 175, payload_bytes)
signature = Ed25519.sign(NEP413_buffer)
```

**CRITICAL**: The signature covers the dynamic payload `pdr_bytes[:-64]`, not a hardcoded offset. This ensures forward compatibility if field sizes change in future versions.

`payment_anchor_type` is inside the signed payload, making PDRs self-verifying — no external metadata channel required.

---

## Internal PDR (193 bytes)

```
Format: <BB16s32s32sQQQ4s8sBH3sB4s
Total:  1 + 1 + 16 + 32 + 32 + 8 + 8 + 8 + 4 + 8 + 1 + 2 + 3 + 1 + 4 + 64 = 193 bytes
```

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 1 | `version` | U8 | `0x03` (both ordinary and bilateral use same internal version; bilateral marked by `signing_mode=0x02`) |
| 1 | 1 | `composite` | U8 | Composite nibble byte (see below) |
| 2 | 16 | `task_id` | bytes(16) | Task UUID |
| 18 | 32 | `agent_account_hash` | bytes(32) | SHA-256 of agent account |
| 50 | 32 | `work_hash` | bytes(32) | SHA-256 of work result |
| 82 | 8 | `timestamp_ns` | U64 | Timestamp in nanoseconds |
| 90 | 8 | `global_seq` | U64 | Global sequence number |
| 98 | 8 | `parent_seq` | U64 | Parent sequence (0 for standard; escrow PROVISIONAL PDR ref for SETTLED) |
| 106 | 4 | `payment_ref` | bytes(4) | First 4 bytes of payment hash (indexing) |
| 110 | 8 | `semantic_anchor` | bytes(8) | Semantic anchor |
| 118 | 1 | `signing_mode` | U8 | `0x01` = VPS |
| 119 | 2 | `reputation_count` | U16 | Reputation counter |
| 121 | 3 | `reserved` | bytes(3) | Reserved |
| 124 | 1 | `sig_scheme` | U8 | `0x01` = Ed25519 |
| 125 | 4 | `expansion_reserved` | bytes(4) | PQ-signature pointer buffer (quantum migration path) |
| 129 | 64 | `signature` | bytes(64) | Ed25519 signature (NEP-413) |

**Payload** = bytes 0–128 (129 bytes). **Signature** = bytes 129–192 (64 bytes).

### Composite Nibble Byte

Byte 1 (`composite`) packs two 4-bit fields:

```
[aaaa bbbb]
  ││││ │││└── pdr_type (bits 3–0)
  └└└┘────── payment_anchor_type (bits 7–4)
```

```python
composite = (payment_anchor_type << 4) | (pdr_type & 0x0F)
pdr_type = composite & 0x0F
payment_anchor_type = (composite >> 4) & 0x0F
```

Backward compatibility: Old PDRs with `composite = 0x00` → UNPAID (0x0) + standard (0x0). Existing Merkle tree proofs remain valid.

### Internal Signature

```
NEP413_buffer = pack("<II129s", 2147484061, 129, internal_payload)
signature = Ed25519.sign(NEP413_buffer)
```

---

## PaymentAnchorType Enum

| Value | Name | Description |
|-------|------|-------------|
| `0x00` | UNPAID | No payment. Blocked on mainnet. Available on testnet. |
| `0x01` | NEAR_DIRECT | Direct NEAR payment |
| `0x02` | AGENT_MARKET_SUBMIT | Reserved |
| `0x03` | AGENT_MARKET_RELEASE | Reserved |
| `0x04` | NEAR_ESCROW_LOCK | Escrow locked (PROVISIONAL PDR) |
| `0x05` | X402_BASE | x402 payment on Base |
| `0x06` | X402_POLYGON | x402 payment on Polygon |
| `0x07` | X402_NEAR | x402 payment on NEAR (future) |
| `0x08` | CHAIN_SIG_PAYMENT | NEAR Chain Signatures payment |
| `0x09` | NEAR_ESCROW_SETTLED | Escrow released (SETTLED PDR) |
| `0x0A–0xFE` | — | Reserved |
| `0xFF` | UNKNOWN | Unrecognized, treat as UNPAID |

All types are flat $0.01 per PDR. The anchor type is a technical attribute, not a pricing tier.

### parent_seq Semantics

- Standard PDRs (NEAR_DIRECT, X402_*): `parent_seq = 0`
- `NEAR_ESCROW_LOCK` (0x04, PROVISIONAL): `parent_seq = 0`
- `NEAR_ESCROW_SETTLED` (0x09, SETTLED): `parent_seq = global_seq` of the original PROVISIONAL PDR, binding SETTLED to PROVISIONAL cryptographically

---

## Version History

### v2.4 (bilateral) — version byte `0x04`

- Same 239-byte external format as v2.3 — no size change
- `payload_hash` semantics: Binding Hash = `sha256(work_hash + sig_A_bytes + agent_pubkey_bytes)`
- Produced when `agent_sig` + `agent_pubkey` are provided in notarize request
- `agent_sig` stored in `notary_ledger.agent_sig` column (TEXT)
- Internal PDR `signing_mode` = `0x02` (bilateral marker)
- Price: $0.01 (same as ordinary)
- Parser: `format_version="v2.4"`, same struct unpack as v2.3

### v2.3 (ordinary) — version byte `0x03`

- Added `payment_anchor_type` field (1 byte) to External PDR at offset 2
- External PDR grew from 238 → 239 bytes
- External payload grew from 174 → 175 bytes
- All subsequent field offsets shifted +1 byte
- `payment_anchor_type` is inside the signed payload (prevents forgery)
- Internal PDR: `composite` byte at offset 1 now explicitly encodes `payment_anchor_type` in high nibble
- `expansion_reserved` (4 bytes) added at Internal offset 125 for quantum migration path

### v2.2 — version byte `0x02`

- External PDR: 238 bytes, no `payment_anchor_type` field
- All PDRs implicitly treated as `NEAR_DIRECT` (0x01) when parsed by v2.3 code
- Internal PDR: `composite` byte existed but `payment_anchor_type` was not explicitly defined in high nibble

### Field Offset Comparison (External PDR)

| Field | v2.2 Offset | v2.3 Offset | Change |
|-------|-------------|-------------|--------|
| `version` | 0 | 0 | `0x02` → `0x03` |
| `sig_scheme` | 1 | 1 | Unchanged |
| `payment_anchor_type` | — | 2 | NEW |
| `timestamp_utc` | 2 | 3 | +1 shift |
| `issuer_id` | 10 | 11 | +1 shift |
| `subject_hash` | 46 | 47 | +1 shift |
| `payload_hash` | 78 | 79 | +1 shift |
| `merkle_root` | 110 | 111 | +1 shift |
| `payment_hash` | 142 | 143 | +1 shift |
| `signature` | 174 | 175 | +1 shift |
| **Total** | **238** | **239** | +1 byte |

---

## Verification

Given a 239-byte external PDR and the notary's Ed25519 public key:

1. Split: `payload = pdr[:-64]`, `sig = pdr[-64:]`
2. Build NEP-413 envelope: `pack("<II", 2147484061, len(payload)) + payload`
3. Verify: `Ed25519.verify(envelope, sig, pubkey)`

See [`pdr_parser.py`](pdr_parser.py) for a standalone implementation.