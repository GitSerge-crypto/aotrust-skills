#!/usr/bin/env python3
"""
AOTrust Notarize — GitHub Action entry point.

Notarizes files via AOTrust free tier API (no wallet needed).
Verifies the returned PDR locally using pdr_parser.py (offline).

Usage:
    python3 notarize.py --files "dist/*" --api-url "https://api.aotrust.link"
    python3 notarize.py --file README.md
"""

import argparse
import base64
import glob
import hashlib
import json
import os
import sys
import urllib.request

# Import pdr_parser from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdr_parser import parse_external_pdr, verify_pdr_signature

NOTARY_PUBKEY_HEX = "490f51f23b993eacaff54fc977d9a7689ab7d4ae91504dc6cbdeadb2dbf1f462"


def compute_sha256(filepath):
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def notarize_file(work_hash, api_url):
    """Call AOTrust free tier API to notarize a work hash."""
    payload = json.dumps({"work_hash": work_hash}).encode("utf-8")
    req = urllib.request.Request(
        f"{api_url}/v1/shield/free",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "AOTrust-Action/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def verify_pdr(pdr_b64):
    """Parse and verify PDR locally (offline)."""
    pdr_bytes = base64.b64decode(pdr_b64)
    parsed = parse_external_pdr(pdr_bytes)
    sig_valid = verify_pdr_signature(pdr_bytes, NOTARY_PUBKEY_HEX)
    return parsed, sig_valid


def main():
    parser = argparse.ArgumentParser(description="AOTrust Notarize GitHub Action")
    parser.add_argument("--files", help="Glob pattern for files to notarize")
    parser.add_argument("--file", help="Single file to notarize")
    parser.add_argument("--api-url", default="https://api.aotrust.link")
    parser.add_argument("--github-output", default=None)
    parser.add_argument("--github-summary", default=None)
    args = parser.parse_args()

    # Resolve files
    if args.file:
        files = [args.file]
    elif args.files:
        files = sorted(glob.glob(args.files))
    else:
        print("Error: --file or --files required", file=sys.stderr)
        sys.exit(1)

    if not files:
        print("Error: no files matched", file=sys.stderr)
        sys.exit(1)

    results = []
    for filepath in files:
        if not os.path.isfile(filepath):
            print(f"Skip: {filepath} (not a file)", file=sys.stderr)
            continue

        work_hash = compute_sha256(filepath)
        print(f"Notarizing: {filepath} (SHA-256: {work_hash[:16]}...)")

        try:
            result = notarize_file(work_hash, args.api_url)
        except Exception as e:
            print(f"API error: {e}", file=sys.stderr)
            sys.exit(1)

        pdr_b64 = result.get("pdr_b64", "")
        shield_id = result.get("shield_id", "")
        tier = result.get("tier", "free")

        # Local verification
        try:
            parsed, sig_valid = verify_pdr(pdr_b64)
            verify_status = "✅ VALID" if sig_valid else "⚠️ Signature NOT verified"
        except Exception as e:
            parsed = None
            sig_valid = False
            verify_status = f"❌ Parse error: {e}"

        pdr_b64_urlsafe = pdr_b64.replace("+", "-").replace("/", "_").rstrip("=")
        verify_url = f"https://verify.aotrust.link/?pdr={pdr_b64_urlsafe}"

        results.append({
            "file": filepath,
            "shield_id": shield_id,
            "verify_url": verify_url,
            "pdr_b64": pdr_b64,
            "sig_valid": sig_valid,
            "tier": tier,
            "timestamp": parsed.timestamp_utc if parsed else None,
        })

        print(f"  Shield ID: {shield_id}")
        print(f"  Tier: {tier}")
        print(f"  Verify: {verify_url}")
        print(f"  Signature: {verify_status}")
        print()

    if not results:
        print("Error: no files notarized", file=sys.stderr)
        sys.exit(1)

    # GitHub outputs (first file for simplicity)
    first = results[0]
    if args.github_output:
        with open(args.github_output, "a") as f:
            f.write(f"shield_id={first['shield_id']}\n")
            f.write(f"verify_url={first['verify_url']}\n")
            f.write(f"pdr_b64={first['pdr_b64']}\n")

    # GitHub step summary (markdown)
    if args.github_summary:
        with open(args.github_summary, "a") as f:
            f.write("## 🛡 AOTrust Notarization\n\n")
            f.write("| File | Shield ID | Tier | Signature | Verify URL |\n")
            f.write("|------|-----------|------|-----------|------------|\n")
            for r in results:
                sig = "✅" if r["sig_valid"] else "❌"
                f.write(f"| `{r['file']}` | `{r['shield_id']}` | {r['tier']} | {sig} | [Verify]({r['verify_url']}) |\n")
            f.write("\n")
    else:
        # Console summary
        print("=" * 60)
        print("AOTrust Notarization Summary")
        print("=" * 60)
        for r in results:
            sig = "✅" if r["sig_valid"] else "❌"
            print(f"  {r['file']}: Shield ID={r['shield_id']} {sig}")
            print(f"    Verify: {r['verify_url']}")
        print("=" * 60)


if __name__ == "__main__":
    main()