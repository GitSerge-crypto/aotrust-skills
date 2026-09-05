# Examples — AOTrust provenance in your AI framework

Copy-paste wrappers that notarize AI outputs with AOTrust (free tier, no API key).

| File | Framework | What it does |
|------|-----------|--------------|
| `langchain_tool.py` | LangChain (`@tool` decorator) | `aotrust_notarize_free` tool for LangChain agents |
| `crewai_notarized_task.py` | CrewAI (`BaseTool` subclass) | `aotrust_notarize_tool` for CrewAI agents |
| `../aotrust-notarize/SKILL.md` | Any MCP client | Full agent guide: quote → pay → notarize → verify |

All wrappers call the same core: `NotaryClient.shield_free(work_hash)` from
[`aotrust-protocol`](https://pypi.org/project/aotrust-protocol/) — free tier,
5 receipts/day per IP, flat $0.01 for volume (x402, Base USDC).

Every receipt (PDR, 239 bytes) is Ed25519-signed by `notary-node.near` and
anchored daily to the NEAR blockchain — verifiable forever, even offline
(see `INTEGRATIONS.md` → "Verify receipts").

Framework imports (`langchain_core`, `crewai`) are intentionally NOT installed
here — each example runs its framework on the user's machine.