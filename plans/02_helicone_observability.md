# Feature: Helicone Observability

**Date:** 2026-05-13
**Status:** 🔄 In Progress

## Description

Add Helicone as a transparent proxy between the app and OpenAI to gain **cost tracking**, **latency monitoring**, **response caching**, and **per-agent usage analytics**. This complements LangSmith (which traces agent graph execution) by providing the financial and operational layer that LangSmith lacks. The integration is minimal — Helicone sits in front of OpenAI, so only `llm.py` and `.env` need core changes.

## Why (Value Added Over LangSmith)

| Capability | LangSmith | Helicone |
|---|---|---|
| Per-request $ cost | ❌ | ✅ |
| Response caching (save $) | ❌ | ✅ |
| Rate limiting at proxy | ❌ | ✅ |
| Cost alerts | ❌ | ✅ |
| Per-agent cost breakdown | ❌ | ✅ (via custom properties) |
| Agent graph tracing | ✅ | ❌ |

**They work together — not as replacements.**

## Checklist

### Phase 1: Core Proxy Setup
- [x] Step 1: Add `HELICONE_API_KEY` to `.env`
- [x] Step 2: Add `HELICONE_ENABLED` toggle to `.env` (default: `true`) — lets students disable if they don't have a key
- [x] Step 3: Modify `get_llm()` in `backend/llm.py` to route through Helicone proxy when enabled
  - Set `base_url="https://oai.helicone.ai/v1"`
  - Add `Helicone-Auth` header
  - Keep direct OpenAI as fallback when `HELICONE_ENABLED=false`

### Phase 2: Per-Agent Custom Properties
- [x] Step 4: Update `call_llm()` signature to accept an optional `agent_name: str` parameter
- [x] Step 5: Pass `Helicone-Property-Agent` header with the agent name so Helicone dashboard shows cost breakdown per agent (Planner, Writer, Critic, etc.)
- [x] Step 6: Update all 6 agent callers to pass their `agent_name` when calling `call_llm()`
  - `planner.py` → `agent_name="Planner"`
  - `reader.py` → `agent_name="Reader"`
  - `writer.py` → `agent_name="Writer"`
  - `critic.py` → `agent_name="Critic"`
  - `compliance.py` → `agent_name="Compliance"`
  - `reflector.py` → (does not call `call_llm` — deterministic, no change needed)

### Phase 3: Caching
- [x] Step 7: Add `Helicone-Cache-Enabled: true` header in `get_llm()` to enable proxy-level response caching
- [ ] Step 8: Test caching — ask the same question twice, verify the second call is faster and shows as cached in Helicone dashboard

### Phase 4: Frontend Helicone Link
- [x] Step 9: Add `helicone_enabled` field to the API response
- [x] Step 10: Show "View in Helicone" link in the run summary when Helicone is enabled

### Phase 5: Testing & Verification
- [ ] Step 11: Add `HELICONE_API_KEY` to `.env` and run full pipeline — verify traces appear in Helicone dashboard
- [ ] Step 12: Run full pipeline with `HELICONE_ENABLED=false` — verify it falls back to direct OpenAI
- [ ] Step 13: Check LangSmith traces still work alongside Helicone (no interference)
- [ ] Step 14: Verify per-agent cost breakdown shows correctly in Helicone UI

## Architecture

```
┌─────────────────────────────────────────────┐
│  Your App (llm.py)                          │
│                                             │
│  HELICONE_ENABLED=true?                     │
│    YES → base_url: oai.helicone.ai/v1       │
│           headers: Helicone-Auth,           │
│                    Helicone-Property-Agent,  │
│                    Helicone-Cache-Enabled    │
│    NO  → base_url: api.openai.com/v1        │
│           (default, no extra headers)        │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌──────────────────────────┐
│  Helicone Proxy          │
│  • Logs request/response │
│  • Calculates $ cost     │
│  • Checks cache          │
│  • Applies rate limits   │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  OpenAI API              │
│  (processes as normal)   │
└──────────────────────────┘
```

## Files Touched

| File | Action | What Changed |
|------|--------|-------------|
| `.env` | Modified | Added `HELICONE_API_KEY`, `HELICONE_ENABLED` |
| `backend/llm.py` | Modified | Proxy routing, custom headers, per-agent property support, caching |
| `backend/agents/planner.py` | Modified | Pass `agent_name="Planner"` to `call_llm()` |
| `backend/agents/reader.py` | Modified | Pass `agent_name="Reader"` to `call_llm()` |
| `backend/agents/writer.py` | Modified | Pass `agent_name="Writer"` to `call_llm()` |
| `backend/agents/critic.py` | Modified | Pass `agent_name="Critic"` to `call_llm()` |
| `backend/agents/compliance.py` | Modified | Pass `agent_name="Compliance"` to `call_llm()` |
| `backend/api.py` | Modified | Added `helicone_enabled` to response, imported flag |
| `frontend/index.js` | Modified | Show "View in Helicone" link in run summary |
| `frontend/index.css` | Modified | Added `.helicone-link` styles |

## Notes

- **No new dependencies** — Helicone works via `base_url` + headers, no SDK needed.
- **LangSmith is unaffected** — `@traceable` decorators and auto-tracing continue to work. The proxy is transparent to LangChain.
- **Reflector skipped** — `reflector.py` is deterministic (no `call_llm`), so no Helicone tagging needed.
- **Caching caveat** — Helicone caches based on exact prompt match. If the writer prompt includes `episodic_memory` from previous iterations, cache won't hit (which is correct behavior).
- **Per-agent headers** — `Helicone-Property-Agent: Writer` lets you filter the Helicone dashboard by agent.
- **Graceful fallback** — If `HELICONE_API_KEY` is missing or `HELICONE_ENABLED=false`, the system works exactly as before.
