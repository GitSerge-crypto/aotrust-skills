"""Tests for pdr_parser.py — v2.3 internal PDR (193 bytes).

Fixture: real mainnet PDR (ledger seq 129), embedded as base64 below.
Public data only — work_hash is a public SHA-256, the signature covers a
public payload. No secrets, no network calls, works offline.
"""
import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdr_parser import (  # noqa: E402
    PDRParseError,
    build_nep413_envelope,
    parse_external_pdr,
    parse_internal_pdr,
)

# Notary Ed25519 public key (published in README / action/notarize.py):
NOTARY_PUBKEY_HEX = "490f51f23b993eacaff54fc977d9a7689ab7d4ae91504dc6cbdeadb2dbf1f462"

# Real mainnet internal PDR (v2.3, 193 bytes, ledger seq 129, public data):
PDR_V23_INTERNAL_B64 = (
    "AwAUQWY50SZGQJQAyxcUAO9eAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAADfsyxGl6oQt48emWbTAJdP"
    "PWtA+xncrwi37VeUeu74vUVD0hgRl9cYAAAAAAAAAAAA"
    "AAAAAAAAAKP7JzsAAAAAAAAAAAEAAAAAAAEAAAAAccpK"
    "mduE7wo6DzUc+WLuSMkZEitla1wfnVU4PibHAvzZkrJ0"
    "WdhGIT6fNm3FE/PooVHnXyEPuFwt+fF1epXAAw=="
)


def _fixture_bytes() -> bytes:
    return base64.b64decode(PDR_V23_INTERNAL_B64)


def test_parse_internal_v23_fields():
    data = _fixture_bytes()
    assert len(data) == 193
    p = parse_internal_pdr(data)
    assert p.version == 3  # v2.3
    assert len(p.work_hash) == 32
    assert p.timestamp_ns > 0
    assert len(p.sig_n) == 64


def test_internal_signature_nep413():
    from nacl.signing import VerifyKey

    p = parse_internal_pdr(_fixture_bytes())
    envelope = build_nep413_envelope(p.payload_bytes)
    # Must not raise:
    VerifyKey(bytes.fromhex(NOTARY_PUBKEY_HEX)).verify(envelope, p.sig_n)


def test_corrupted_signature_fails():
    from nacl.signing import VerifyKey

    p = parse_internal_pdr(_fixture_bytes())
    bad_sig = bytearray(p.sig_n)
    bad_sig[0] ^= 0xFF
    envelope = build_nep413_envelope(p.payload_bytes)
    with pytest.raises(Exception):
        VerifyKey(bytes.fromhex(NOTARY_PUBKEY_HEX)).verify(envelope, bytes(bad_sig))


def test_external_size_guard():
    # 193B is the internal format; the external parser must reject it:
    with pytest.raises(PDRParseError):
        parse_external_pdr(_fixture_bytes())