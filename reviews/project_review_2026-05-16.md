# Project Review

## Findings

### High: The API returns rejected drafts as if they were final successful answers

- [backend/orchestrator.py](/Users/macbookpro/Documents/agents/backend/orchestrator.py:234) routes to `END` once `iterations >= max_iterations`, even when `approved` is still `False`.
- [backend/api.py](/Users/macbookpro/Documents/agents/backend/api.py:92) then copies the last draft into `final_answer` and returns HTTP 200 without exposing the failed approval state.
- [frontend/index.js](/Users/macbookpro/Documents/agents/frontend/index.js:81) always renders `final_answer` as success, so the UI cannot distinguish an approved answer from one that exhausted the loop and still failed review.

This means users can receive an answer that the system itself rejected, with no signal that quality checks failed. At minimum, the API should return `approved` and `issues`, and the backend should decide whether to fail the request or mark the result as incomplete when the critic never approves.

### High: `/research` is declared async but runs the entire blocking pipeline inline

- [backend/api.py](/Users/macbookpro/Documents/agents/backend/api.py:61) defines an `async` route, but [backend/api.py](/Users/macbookpro/Documents/agents/backend/api.py:78) calls `graph.invoke(...)` directly.
- The graph performs blocking LLM and search I/O through [backend/llm.py](/Users/macbookpro/Documents/agents/backend/llm.py:98) and [backend/tools/search.py](/Users/macbookpro/Documents/agents/backend/tools/search.py:27).
- Sensitive runs also call [backend/orchestrator.py](/Users/macbookpro/Documents/agents/backend/orchestrator.py:208) `time.sleep(3)`.

Under concurrent traffic, this will block the FastAPI event loop instead of yielding, so one slow request can stall unrelated requests. If the route stays async, the blocking work needs to be moved to a threadpool or converted to an async execution path.

### Medium: The “Reader” never reads source content, only search snippets

- [backend/agents/reader.py](/Users/macbookpro/Documents/agents/backend/agents/reader.py:18) builds its context exclusively from `title` and `snippet`.
- Those snippets come from DuckDuckGo result metadata in [backend/agents/searcher.py](/Users/macbookpro/Documents/agents/backend/agents/searcher.py:25) and [backend/tools/search.py](/Users/macbookpro/Documents/agents/backend/tools/search.py:14).

That makes the “deep reading” path materially different from what the project description promises. For comparative or nuanced questions, the system is still summarizing search-result blurbs, which is a weak evidence base and will encourage hallucinated specificity.

### Medium: Search failures are silently flattened into “no results”

- [backend/tools/search.py](/Users/macbookpro/Documents/agents/backend/tools/search.py:26) catches all exceptions and [backend/tools/search.py](/Users/macbookpro/Documents/agents/backend/tools/search.py:31) returns `[]`.

This removes the distinction between “the web search found nothing” and “the search tool failed.” The rest of the pipeline then proceeds as though the empty source set were a valid research outcome. That makes outages and dependency regressions hard to detect, and it compounds the first issue because the system can keep drafting from zero evidence and still return a 200 response.

### Medium: Request and response payloads are logged verbatim, including sensitive answers

- [backend/api.py](/Users/macbookpro/Documents/agents/backend/api.py:63) logs the full incoming payload.
- [logger/middleware.py](/Users/macbookpro/Documents/agents/logger/middleware.py:25) logs the full outgoing `/research` response body.

Because the app explicitly supports medical, legal, and financial prompts, this will ship high-stakes user content into logs with no redaction strategy. That is risky even for a teaching project once it is deployed anywhere outside a local laptop.

### Low: The public docs describe an API/UI flow that no longer exists

- [README.md](/Users/macbookpro/Documents/agents/README.md:18) references an approve endpoint.
- [README.md](/Users/macbookpro/Documents/agents/README.md:31) says `api.py` provides SSE streaming.
- [README.md](/Users/macbookpro/Documents/agents/README.md:65) says the HITL gate pauses for user approval and [README.md](/Users/macbookpro/Documents/agents/README.md:66) says the answer is streamed via SSE.

The code now exposes a single request/response POST endpoint and the HITL step auto-approves after a delay. This is not a runtime bug, but it will mislead students about what they are supposed to learn from the repository.

## Open Questions

- Should `max_iterations` be allowed to end in a user-visible failure state, or is the intent to keep retrying until approval?
- Is the project meant to teach “snippet synthesis” or actual retrieval and reading of source documents? The current implementation teaches the former, while the docs describe the latter.

## Verification

- Reviewed the backend orchestration, agents, tools, API, logging, and frontend code paths directly.
- Import sanity checks passed with `python3` for `backend.api` and graph compilation.
- I did not run end-to-end requests because the pipeline depends on external LLM and search services that are not available in this sandboxed session.
