# AOTrust — Skills

Public skills directory for the AOTrust notary service.

## Skills

### aotrust-notarize
Cryptographic notarization for AI agent work output. Flat $0.01 per PDR. See docs.aotrust.link
- [SKILL.md](aotrust-notarize/SKILL.md)
- MCP server: `https://api.aotrust.link/mcp`
- NEAR handle: `aotrust`

## PDR Specification & Tools

### [pdr-spec.md](pdr-spec.md)
PDR v2.3 binary format specification — Internal (193B) and External (239B) structures, field offsets, PaymentAnchorType enum, NEP-413 signature scheme, and version history (v2.2 → v2.3).

### [pdr_parser.py](pdr_parser.py)
Standalone PDR parser and signature verifier. Zero AOTrust dependencies, works offline. Parses v2.2 and v2.3 external PDRs, verifies Ed25519/NEP-413 signatures given a public key. Run: `python3 pdr_parser.py <pdr_b64_or_hex> [notary_pubkey_hex]`