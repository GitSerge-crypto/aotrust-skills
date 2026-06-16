"""
AOTrust PDR v2.3 — Standalone Parser

Parses and verifies Provenance Data Records (PDRs) without any AOTrust dependencies.
Works offline — no network calls required.

Usage:
    >>> from pdr_parser import parse_external_pdr, verify_pdr_signature
    >>> import base64
    >>>
    >>> pdr_b64 = "AwEFA1kuagAAAABub3..."
    >>> pdr_bytes = base64.b64decode(pdr_b64)
    >>> parsed = parse_external_pdr(pdr_bytes)
    >>> print(f"Version: {parsed.format_version}")
    >>> print(f"Timestamp: {parsed.timestamp_utc}")
    >>> print(f"Work hash: {parsed.payload_hash.hex()}")
    >>>
    >>> # Verify signature (requires notary public key)
    >>> pubkey_hex = "490f51f23b993eacaff54fc977d9a7689ab7d4ae91504dc6cbdeadb2dbf1f462"
    >>> is_valid = verify_pdr_signature(pdr_bytes, pubkey_hex)
    >>> print(f"Signature valid: {is_valid}")

Requires: nacl (pynacl) for signature verification only. Parsing works without it.
"""

import struct
from dataclasses import dataclass


PAYMENT_ANCHOR_TYPES = {
    0x00: "UNPAID",
    0x01: "NEAR_DIRECT",
    0x02: "AGENT_MARKET_SUBMIT",
    0x03: "AGENT_MARKET_RELEASE",
    0x04: "NEAR_ESCROW_LOCK",
    0x05: "X402_BASE",
    0x06: "X402_POLYGON",
    0x07: "X402_NEAR",
    0x08: "CHAIN_SIG_PAYMENT",
    0x09: "NEAR_ESCROW_SETTLED",
    0xFF: "UNKNOWN",
}

NEP413_TAG = 2147484061

EXTERNAL_PDR_SIZE = 239
EXTERNAL_PAYLOAD_SIZE = 175
INTERNAL_PDR_SIZE = 193
INTERNAL_PAYLOAD_SIZE = 129
ED25519_SIG_SIZE = 64


class PDRParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedExternalPDR:
    version: int
    sig_scheme: int
    payment_anchor_type: int
    timestamp_utc: int
    issuer_id: bytes
    subject_hash: bytes
    payload_hash: bytes
    merkle_root: bytes
    payment_hash: bytes
    sig_n: bytes
    payload_bytes: bytes
    format_version: str

    @property
    def payment_anchor_name(self) -> str:
        return PAYMENT_ANCHOR_TYPES.get(self.payment_anchor_type, f"UNKNOWN(0x{self.payment_anchor_type:02x})")

    @property
    def issuer_id_str(self) -> str:
        return self.issuer_id.replace(b"\x00", b"").decode("utf-8", errors="replace")

    @property
    def timestamp_iso(self) -> str:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(self.timestamp_utc, tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class ParsedInternalPDR:
    version: int
    composite: int
    task_id: bytes
    agent_account_hash: bytes
    work_hash: bytes
    timestamp_ns: int
    global_seq: int
    parent_seq: int
    payment_ref: bytes
    semantic_anchor: bytes
    signing_mode: int
    reputation_count: int
    reserved: bytes
    sig_scheme: int
    expansion_reserved: bytes
    sig_n: bytes
    payload_bytes: bytes

    @property
    def payment_anchor_type(self) -> int:
        return (self.composite >> 4) & 0x0F

    @property
    def pdr_type(self) -> int:
        return self.composite & 0x0F


def parse_external_pdr(data: bytes) -> ParsedExternalPDR:
    """Parse an external PDR (239 bytes for v2.3, 238 bytes for v2.2)."""
    if not isinstance(data, (bytes, bytearray)):
        raise PDRParseError(f"Expected bytes/bytearray, got {type(data).__name__}")
    if len(data) < 1:
        raise PDRParseError("PDR data is empty")

    version = data[0]

    if version == 0x03:
        if len(data) != EXTERNAL_PDR_SIZE:
            raise PDRParseError(
                f"v2.3 PDR size mismatch: got {len(data)}, expected {EXTERNAL_PDR_SIZE}"
            )
        payload_bytes = data[:EXTERNAL_PAYLOAD_SIZE]
        sig_n = data[EXTERNAL_PAYLOAD_SIZE:EXTERNAL_PAYLOAD_SIZE + ED25519_SIG_SIZE]
        (ver, sig_scheme, pat_byte, ts, issuer, subject_hash, payload_hash,
         merkle_root, payment_hash) = struct.unpack_from(
            "<BBBQ36s32s32s32s32s", data, offset=0
        )
        return ParsedExternalPDR(
            version=ver,
            sig_scheme=sig_scheme,
            payment_anchor_type=pat_byte,
            timestamp_utc=ts,
            issuer_id=issuer,
            subject_hash=subject_hash,
            payload_hash=payload_hash,
            merkle_root=merkle_root,
            payment_hash=payment_hash,
            sig_n=sig_n,
            payload_bytes=payload_bytes,
            format_version="v2.3",
        )
    elif version == 0x02:
        v22_size = 238
        v22_payload_size = 174
        if len(data) != v22_size:
            raise PDRParseError(
                f"v2.2 PDR size mismatch: got {len(data)}, expected {v22_size}"
            )
        payload_bytes = data[:v22_payload_size]
        sig_n = data[v22_payload_size:v22_payload_size + ED25519_SIG_SIZE]
        (ver, sig_scheme, ts, issuer, subject_hash, payload_hash,
         merkle_root, payment_hash) = struct.unpack_from(
            "<BBQ36s32s32s32s32s", data, offset=0
        )
        return ParsedExternalPDR(
            version=ver,
            sig_scheme=sig_scheme,
            payment_anchor_type=1,
            timestamp_utc=ts,
            issuer_id=issuer,
            subject_hash=subject_hash,
            payload_hash=payload_hash,
            merkle_root=merkle_root,
            payment_hash=payment_hash,
            sig_n=sig_n,
            payload_bytes=payload_bytes,
            format_version="v2.2",
        )
    else:
        raise PDRParseError(f"Unknown PDR version: {version:#04x}")


def parse_internal_pdr(data: bytes) -> ParsedInternalPDR:
    """Parse an internal PDR (193 bytes)."""
    if not isinstance(data, (bytes, bytearray)):
        raise PDRParseError(f"Expected bytes/bytearray, got {type(data).__name__}")
    if len(data) != INTERNAL_PDR_SIZE:
        raise PDRParseError(
            f"Internal PDR size mismatch: got {len(data)}, expected {INTERNAL_PDR_SIZE}"
        )
    payload_bytes = data[:INTERNAL_PAYLOAD_SIZE]
    sig_n = data[INTERNAL_PAYLOAD_SIZE:]
    (ver, composite, task_id, agent_account_hash, work_hash, timestamp_ns,
     global_seq, parent_seq, payment_ref, semantic_anchor, signing_mode,
     reputation_count, reserved, sig_scheme,
     expansion_reserved) = struct.unpack_from(
        "<BB16s32s32sQQQ4s8sBH3sB4s", data, offset=0
    )
    return ParsedInternalPDR(
        version=ver,
        composite=composite,
        task_id=task_id,
        agent_account_hash=agent_account_hash,
        work_hash=work_hash,
        timestamp_ns=timestamp_ns,
        global_seq=global_seq,
        parent_seq=parent_seq,
        payment_ref=payment_ref,
        semantic_anchor=semantic_anchor,
        signing_mode=signing_mode,
        reputation_count=reputation_count,
        reserved=reserved,
        sig_scheme=sig_scheme,
        expansion_reserved=expansion_reserved,
        sig_n=sig_n,
        payload_bytes=payload_bytes,
    )


def build_nep413_envelope(payload: bytes) -> bytes:
    """Build NEP-413 envelope: pack('<II', TAG, len(payload)) + payload."""
    envelope = bytearray(4 + 4 + len(payload))
    struct.pack_into("<II", envelope, 0, NEP413_TAG, len(payload))
    envelope[8:] = payload
    return bytes(envelope)


def verify_pdr_signature(pdr_bytes: bytes, notary_pubkey_hex: str) -> bool:
    """
    Verify the Ed25519 signature on an external PDR using NEP-413 envelope.

    Args:
        pdr_bytes: Raw PDR bytes (239 for v2.3, 238 for v2.2)
        notary_pubkey_hex: Hex-encoded Ed25519 public key of the notary

    Returns:
        True if signature is valid, False otherwise

    Requires: pynacl (pip install pynacl)
    """
    try:
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignatureError
    except ImportError:
        raise ImportError(
            "pynacl is required for signature verification. "
            "Install with: pip install pynacl"
        )

    parsed = parse_external_pdr(pdr_bytes)
    envelope = build_nep413_envelope(parsed.payload_bytes)

    try:
        verify_key = VerifyKey(bytes.fromhex(notary_pubkey_hex))
        verify_key.verify(envelope, parsed.sig_n)
        return True
    except BadSignatureError:
        return False


def _decode_pdr_input(raw_arg: str, fmt: str = "auto") -> bytes:
    """Decode a PDR from base64 or hex string.

    Args:
        raw_arg: Base64 or hex-encoded PDR bytes.
        fmt: "base64", "hex", or "auto" (try base64 first, then hex).

    Returns:
        Decoded PDR bytes.

    Raises:
        PDRParseError: If decoding fails or result is not a valid PDR.
    """
    import base64 as _base64

    VALID_SIZES = {EXTERNAL_PDR_SIZE, 238, INTERNAL_PDR_SIZE}
    VALID_VERSIONS = {0x02, 0x03}

    def _try_base64(s: str) -> bytes:
        padded = s + "=" * ((4 - len(s) % 4) % 4)
        return _base64.b64decode(padded)

    def _try_hex(s: str) -> bytes:
        if len(s) % 2 != 0 or not all(c in "0123456789abcdefABCDEF" for c in s):
            raise ValueError("not valid hex")
        return bytes.fromhex(s)

    def _looks_like_pdr(data: bytes) -> bool:
        return len(data) in VALID_SIZES and data[0] in VALID_VERSIONS

    if fmt == "base64":
        return _try_base64(raw_arg)

    if fmt == "hex":
        return _try_hex(raw_arg)

    # auto: try base64 first (most common), then hex, validate result
    for decode_fn, label in [(_try_base64, "base64"), (_try_hex, "hex")]:
        try:
            data = decode_fn(raw_arg)
            if _looks_like_pdr(data):
                return data
        except Exception:
            continue

    # Neither produced a valid PDR — try both without validation and report errors
    errors = {}
    for label, decode_fn in [("base64", _try_base64), ("hex", _try_hex)]:
        try:
            data = decode_fn(raw_arg)
            errors[label] = (
                f"decoded {len(data)} bytes, version 0x{data[0]:02x} "
                f"(expected v0x02 or v0x03, size 238/239/193)"
            )
        except Exception as e:
            errors[label] = str(e)

    parts = [f"{k}: {v}" for k, v in errors.items()]
    raise PDRParseError(
        f"Input does not decode to a valid PDR. Tried: {'; '.join(parts)}"
    )


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Parse and optionally verify an AOTrust PDR (v2.2/v2.3)."
    )
    parser.add_argument(
        "--pdr",
        required=True,
        help="PDR data, base64 or hex encoded",
    )
    parser.add_argument(
        "--pubkey",
        default=None,
        help="Ed25519 public key (hex) for signature verification",
    )
    parser.add_argument(
        "--format",
        choices=["auto", "base64", "hex"],
        default="auto",
        help="Input encoding format (default: auto-detect)",
    )
    args = parser.parse_args()

    try:
        pdr_bytes = _decode_pdr_input(args.pdr, args.format)
    except PDRParseError as e:
        print(f"Decode error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Decode error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        parsed = parse_external_pdr(pdr_bytes)
    except PDRParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"PDR Format:    {parsed.format_version}")
    print(f"Version:       0x{parsed.version:02x}")
    print(f"Sig Scheme:    0x{parsed.sig_scheme:02x} ({'Ed25519' if parsed.sig_scheme == 1 else 'Unknown'})")
    print(f"Payment Type:  0x{parsed.payment_anchor_type:02x} ({parsed.payment_anchor_name})")
    print(f"Timestamp:     {parsed.timestamp_utc} ({parsed.timestamp_iso})")
    print(f"Issuer:        {parsed.issuer_id_str}")
    print(f"Subject Hash:  {parsed.subject_hash.hex()}")
    print(f"Payload Hash:  {parsed.payload_hash.hex()}")
    print(f"Merkle Root:   {parsed.merkle_root.hex()}")
    print(f"Payment Hash:  {parsed.payment_hash.hex()}")
    print(f"Signature:     {parsed.sig_n.hex()[:32]}...")

    if args.pubkey:
        try:
            valid = verify_pdr_signature(pdr_bytes, args.pubkey)
            print(f"Signature:     {'VALID' if valid else 'INVALID'}")
        except ImportError as e:
            print(f"Signature:     skipped ({e})")