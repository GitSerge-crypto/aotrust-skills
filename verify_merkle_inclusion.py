#!/usr/bin/env python3
"""Offline Merkle inclusion proof verification for AOTrust PDRs.

Standalone, dependency-free (stdlib only). Implements the official
RFC 9162 Section 2.1.3.2 (Certificate Transparency) MERKLE AUDIT PATH
verification walk.

Verify that a leaf (the SHA-256 of a notarized work's reputation slice)
is provably included in the daily anchor tree whose Merkle root is
committed on-chain in the NEAR contract `notary-node.near`.

Trust model:
  - The daily root is readable from ANY public NEAR RPC endpoint
    (contract method `get_root`), independent of AOTrust servers.
  - The inclusion proof is returned by the AOTrust verify API
    (fields: merkle_proof, merkle_index, merkle_leaf, merkle_tree_size).
    Save the verify JSON response — you can re-verify it forever, offline,
    with this script and no AOTrust server.

Hashing (must match the anchoring engine, RFC 9162):
  - Leaf:   SHA-256(0x00 || leaf_data)
  - Node:   SHA-256(0x01 || left || right)

Usage:
  python3 verify_merkle_inclusion.py \
      --leaf <hex32> --proof <hex32,hex32,...> --index <int> \
      --root <hex32> --tree-size <int>

  --leaf       final leaf value, hex64 (hash_leaf of the work hash slice)
  --proof      comma-separated proof hashes (hex64), in the order returned
               by the AOTrust verify API (merkle_proof field)
  --index      0-based position of the leaf in the tree (merkle_index)
  --root       expected Merkle root, hex64 (PDR merkle_root / on-chain root)
  --tree-size  total number of leaves in the anchored tree
               (merkle_tree_size from the verify API response)

Exit codes: 0 = VALID, 1 = INVALID or usage/parse error.

Example:
  python3 verify_merkle_inclusion.py \
    --leaf 2e3aa189e1f666b2c3e864e21d978388020b89a6725e31ff2657bad5840a7f02 \
    --proof 70c2e612049c44d5947db6e3a8802a2050a16f0d303ac40ba294da811768a9eb \
    --index 0 \
    --root 2c37c5cacd334ac863756947650e18cfab41f61b0cf84b28342489292060ba4f \
    --tree-size 2
  → VALID
"""

import argparse
import hashlib
import sys


def _hash_leaf(data: bytes) -> bytes:
    """RFC 9162 leaf hash: SHA-256(0x00 || data)."""
    return hashlib.sha256(b"\x00" + data).digest()


def _hash_node(left: bytes, right: bytes) -> bytes:
    """RFC 9162 node hash: SHA-256(0x01 || left || right)."""
    return hashlib.sha256(b"\x01" + left + right).digest()


def _parse_hex32(s: str, name: str) -> bytes:
    s = s.strip().lower().replace("0x", "")
    try:
        raw = bytes.fromhex(s)
    except ValueError:
        raise ValueError(f"{name}: invalid hex")
    if len(raw) != 32:
        raise ValueError(f"{name}: expected 32 bytes (64 hex chars), got {len(raw)}")
    return raw


def verify(leaf_hex: str, proof_hex: str, index: int, root_hex: str, tree_size: int) -> bool:
    """Official RFC 9162 Section 2.1.3.2 inclusion-verification walk.

    tree_size is REQUIRED: the (fn, sn) walk depends on the total leaf
    count of the tree, which cannot be derived from the root alone.
    """
    leaf = _parse_hex32(leaf_hex, "leaf")
    expected_root = _parse_hex32(root_hex, "root")
    proof = (
        [_parse_hex32(p, "proof element") for p in proof_hex.split(",") if p.strip()]
        if proof_hex.strip()
        else []
    )

    if tree_size < 1:
        return False
    if index < 0 or index >= tree_size:
        return False

    fn = index          # position of the leaf in the subtree under review
    sn = tree_size - 1  # position of the last leaf in the subtree under review
    r = leaf

    for p in proof:
        if sn == 0:
            return False  # proof longer than the tree allows
        if (fn & 1) == 1 or fn == sn:
            # sibling is on the LEFT
            r = _hash_node(p, r)
            if (fn & 1) == 0:
                while fn > 0 and (fn & 1) == 0:
                    fn >>= 1
                    sn >>= 1
        else:
            # sibling is on the RIGHT
            r = _hash_node(r, p)
        fn >>= 1
        sn >>= 1

    # The walk must terminate exactly at the tree root: (fn, sn) == (0, 0).
    # Without this check a proof shorter than the tree depth (e.g. a wrong
    # --tree-size) could falsely validate (RFC 9162 §2.1.3.2 completeness).
    if fn != 0 or sn != 0:
        return False
    return r == expected_root


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify a Merkle inclusion proof (RFC 9162) for an AOTrust anchored PDR"
    )
    parser.add_argument("--leaf", required=True,
                        help="final leaf value (32-byte hex; hash_leaf of the work hash)")
    parser.add_argument("--proof", default="",
                        help="comma-separated proof hashes (hex64), merkle_proof from the verify API")
    parser.add_argument("--index", type=int, required=True,
                        help="leaf index in the tree (merkle_index)")
    parser.add_argument("--root", required=True,
                        help="expected merkle root (32-byte hex; PDR merkle_root / on-chain root)")
    parser.add_argument("--tree-size", type=int, required=True,
                        help="total leaf count of the anchored tree (merkle_tree_size)")
    args = parser.parse_args()

    try:
        ok = verify(args.leaf, args.proof, args.index, args.root, args.tree_size)
    except ValueError as e:
        print(f"INVALID (parse error: {e})")
        sys.exit(1)

    if ok:
        print("VALID")
        sys.exit(0)
    else:
        print("INVALID")
        sys.exit(1)


if __name__ == "__main__":
    main()