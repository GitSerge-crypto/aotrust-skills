#!/usr/bin/env python3
"""Free tier: notarize without API key or wallet — then check status by job_id.

The free channel (`shield_free()`) needs NO api_key and NO wallet.
Returns a job_id immediately. Free PDRs are NEAR-anchored in batches
(the anchor timer runs periodically), so right after the call the status
may still be PENDING and turn anchored a few minutes later. `wait_for_pdr()`
works if you are willing to wait for the next anchor batch; `get_pdr()`
returns the signed PDR immediately either way.

IMPORTANT: base_url must be https://api.aotrust.link — WITHOUT /v1.
The SDK appends /v1/... paths itself. Passing a URL that already ends
in /v1 produces /v1/v1/... → HTTP 404 on every call.
"""

import asyncio
import hashlib
import sys
import uuid
from datetime import datetime, timezone

from agent_notary import NotaryClient

# base_url WITHOUT /v1 — see module docstring.
client = NotaryClient(base_url="https://api.aotrust.link")


async def main() -> None:
    # 1. Hash the artifact (any bytes: text, file, JSON...).
    artifact = f"free-tier demo {datetime.now(timezone.utc).isoformat()}".encode()
    work_hash = hashlib.sha256(artifact).hexdigest()

    # 2. Notarize on the free tier. The response contains job_id —
    #    THIS is the handle for every later status/verify call (a UUID,
    #    not the artifact text).
    result = await client.shield_free(work_hash)
    job_id = result["job_id"]
    print(f"[1/3] Notarized (tier={result.get('tier', 'free')})")
    print(f"      job_id   = {job_id}")
    print(f"      shield_id= {result.get('shield_id', 'N/A')}")

    # 3. Check status by job_id. It may be PENDING right after the call and
    #    turn anchored when the next anchor batch lands (a few minutes).
    status = await client.get_status(job_id)
    print(f"[2/3] Status by job_id: {status.status}")

    # 4. Fetch the PDR and verify it — works immediately, no waiting.
    pdr = await client.get_pdr(job_id)
    print(f"[3/3] PDR received ({len(pdr.pdr_b64)} chars base64)")
    print(f"      Verify in browser: {pdr.verify_url}")

    try:
        server = await client.verify_pdr(pdr.pdr_b64)
        print(f"      Server-side verification: {server}")
    except Exception as exc:  # noqa: BLE001 — demo keeps running on verify hiccups
        print(f"      Server-side verification skipped: {exc}")

    # Save job_id somewhere persistent if you want to check it later.
    print(f"      (job_id is a UUID like {uuid.UUID(job_id)} — keep it, not the artifact text)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        hint = str(exc)
        if "429" in hint or "LIMIT" in hint.upper():
            print("Free tier = 5 PDR / 24h per IP. Retry tomorrow or use the paid tier.")
        sys.exit(1)
    sys.exit(0)