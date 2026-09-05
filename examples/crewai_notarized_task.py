#!/usr/bin/env python3
"""CrewAI custom Tool: notarize task outputs with AOTrust (free tier).

Copy-paste this into your project and attach `aotrust_notarize_tool` to any
agent whose output you want provable (e.g. the researcher's final report).

Requires: pip install aotrust-protocol crewai
"""

import asyncio
import hashlib

from crewai.tools import BaseTool

from agent_notary import NotaryClient

_client = NotaryClient(base_url="https://api.aotrust.link/v1")


class AOTrustNotarizeTool(BaseTool):
    """Notarize a task output: creates a signed cryptographic receipt (PDR)
    proving the artifact existed at this moment. Free tier, no API key."""

    name: str = "aotrust_notarize"
    description: str = (
        "Notarize final task output (text). Returns a shield_id and a verify URL "
        "for a signed PDR receipt anchored to the NEAR blockchain."
    )

    def _run(self, artifact_text: str) -> str:
        work_hash = hashlib.sha256(artifact_text.encode("utf-8")).hexdigest()
        res = asyncio.run(_client.shield_free(work_hash))
        shield_id = res.get("shield_id", "?")
        verify_url = res.get("verify_url", f"https://verify.aotrust.link/?pdr={res.get('pdr_b64', '')}")
        return (
            f"Notarized. shield_id={shield_id} (work_hash={work_hash[:12]}...). "
            f"Verify: {verify_url}"
        )


aotrust_notarize_tool = AOTrustNotarizeTool()

if __name__ == "__main__":
    # Smoke: run the tool directly
    print(aotrust_notarize_tool.run(artifact_text="crewai output example"))