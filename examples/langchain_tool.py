#!/usr/bin/env python3
"""LangChain tool wrapper: notarize any artifact with AOTrust (free tier).

Copy-paste this into your project, adjust the artifact source, and the
`AOTrustNotarizeTool` becomes available to your LangChain agents.

Requires: pip install aotrust-protocol langchain-core
"""

import asyncio
import hashlib

from langchain_core.tools import tool

from agent_notary import NotaryClient

_client = NotaryClient(base_url="https://api.aotrust.link/v1")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@tool
def aotrust_notarize_free(artifact_text: str) -> str:
    """Notarize an artifact: creates a signed cryptographic receipt (PDR)
    proving the artifact existed at this moment. Anchored daily to NEAR.
    Free tier, no API key needed (5 receipts/day per IP).

    Args:
        artifact_text: the text/content of the artifact to notarize
            (e.g. generated code, a report, a contract summary).

    Returns:
        A short provenance statement: shield_id + verify URL.
    """
    work_hash = _sha256_hex(artifact_text.encode("utf-8"))
    res = asyncio.run(_client.shield_free(work_hash))
    shield_id = res.get("shield_id", "?")
    verify_url = res.get("verify_url", f"https://verify.aotrust.link/?pdr={res.get('pdr_b64', '')}")
    return (
        f"Notarized. shield_id={shield_id} (work_hash={work_hash[:12]}...). "
        f"Verify: {verify_url}"
    )


if __name__ == "__main__":
    # Smoke: run the tool directly
    print(aotrust_notarize_free.invoke({"artifact_text": "hello provenance"}))