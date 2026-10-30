#!/usr/bin/env python3
"""AOTrust notary — MCP server (stdio), runnable straight from this repository.

Why this file exists
--------------------
Glama's MCP directory grades a repository listing only when it can build and run
a real server from it and enumerate its tools (Tool Definition Quality Score,
TDQS). `aotrust-skills` carried skills, specs and a client-side parser, but no
runnable server — so the listing stayed "quality: not evaluated" indefinitely.
This is a thin, dependency-light stdio facade over the public AOTrust HTTP API:
no keys, no database, read-only except `notarize_free` (free tier, 5/24h per IP).

Tools:
  notary_status   — anchor state and price list
  notary_quote    — price for a work_hash (free)
  notarize_free   — free proof of existence for a SHA-256 hash
  verify_pdr      — server-side verification of a PDR blob
  shield_lookup   — public receipt lookup by 8-hex Shield ID

Run:
  pip install "mcp>=1.2" && python mcp_server.py
  # or: docker build -t aotrust-notary . && docker run -i aotrust-notary

Environment:
  AOTRUST_BASE_URL   default https://api.aotrust.link/v1
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE = os.environ.get("AOTRUST_BASE_URL", "https://api.aotrust.link/v1").rstrip("/")
UA = "aotrust-skills-mcp/1.0 (+https://docs.aotrust.link)"
TIMEOUT = 20


def _req(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET/POST against the public API; errors are returned as data, never raised."""
    url = f"{BASE}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                headers={"Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        detail = e.read()[:600].decode("utf-8", "replace")
        return {"error": f"HTTP {e.code}", "detail": detail}
    except Exception as e:  # noqa: BLE001 - a tool must answer, not crash
        return {"error": type(e).__name__, "detail": str(e)}


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def main() -> None:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("aotrust-notary")

    @mcp.tool()
    def notary_status() -> dict:
        """Anchor state and prices: confirm the notary is live before notarizing.

        Returns the current cumulative Merkle-log anchor (sequence, size, root,
        NEAR transaction) plus the price list in USDC on Base via x402:
        PDR $0.01, evidence bundle $0.02, signed time $0.002. The free tier
        covers 5 receipts per IP per 24 hours and needs no account.
        """
        return {
            "anchor": _req("GET", "/anchor/status"),
            "health_url": "https://api.aotrust.link/health",
            "prices_usdc": {"pdr": "0.01", "bundle": "0.02", "signed_time": "0.002"},
            "network": "eip155:8453 (Base, USDC)",
            "free_tier": "5 receipts / 24h / IP",
        }

    @mcp.tool()
    def notary_quote(work_hash: str) -> dict:
        """Price a single notarization for an artifact, identified by its SHA-256.

        Args:
            work_hash: lowercase hex SHA-256 of the artifact, exactly 64 characters.
        """
        if len(work_hash) != 64:
            return {"error": "work_hash must be 64 hex chars (SHA-256)"}
        return _req("POST", "/notarize/quote", {"work_hash": work_hash})

    @mcp.tool()
    def notarize_free(work_hash: str, metadata: str = "") -> dict:
        """Create a free proof of existence (PDR) for an artifact hash — no payment.

        Returns a signed 239-byte PDR, an 8-hex Shield ID and a public verify URL;
        the receipt joins the hourly cumulative Merkle log anchored to NEAR
        Mainnet. Replay within 24h from the same IP returns the original receipt
        with `already_exists: true`.

        Args:
            work_hash: lowercase hex SHA-256 of the artifact, exactly 64 characters.
            metadata: optional short label (agent or project name) stored with the receipt.
        """
        if len(work_hash) != 64:
            return {"error": "work_hash must be 64 hex chars (SHA-256)"}
        body: dict[str, Any] = {"work_hash": work_hash}
        if metadata:
            body["metadata"] = metadata
        return _req("POST", "/shield/free", body)

    @mcp.tool()
    def verify_pdr(pdr_b64: str) -> dict:
        """Verify a PDR receipt and read its fields, signature and payment status.

        Works offline-equivalent: the server re-checks the Ed25519 signature over
        the NEP-413 envelope and, for paid receipts, the on-chain payment.

        Args:
            pdr_b64: the receipt as base64 (URL-safe or standard, padding optional).
        """
        token = urllib.parse.quote(pdr_b64.strip(), safe="")
        return _req("GET", f"/pdr/verify/{token}")

    @mcp.tool()
    def shield_lookup(shield_id: str) -> dict:
        """Look up a public receipt by its 8-hex Shield ID (for example 228c16fd).

        Returns the timestamp, payment rail, PDR version and the PDR blob itself.
        This is a read-only public lookup: anyone can verify a receipt without an
        account, matching https://verify.aotrust.link.
        """
        sid = shield_id.strip().lower()
        if len(sid) != 8:
            return {"error": "shield_id must be 8 hex chars"}
        return _req("GET", f"/shield/lookup/{sid}")

    mcp.run()


if __name__ == "__main__":
    main()
