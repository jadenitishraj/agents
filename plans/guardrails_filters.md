# Feature: Guardrails AI Input/Output Filtering

**Date:** 2026-05-16
**Status:** ✅ Implemented

## Description

Implement robust input and output filtering for the LangGraph multi-agent application using Guardrails AI. This module will validate both user inputs and LLM outputs to prevent prompt injections, PII leaks, toxic language, and custom banned words. To maintain system stability, it will catch all validation exceptions and return safe, structured user-facing messages rather than crashing the orchestrator.

**Strict Modularity Requirement:** The code inside the `backend/guardrails` directory must be highly modular. No single file should exceed 20 to 30 lines. The architecture will be divided into small, single-responsibility files (e.g., config, pipeline orchestrator, individual validators).

## Checklist

- [x] Step 1: Update `backend/requirements.txt` to include `guardrails-ai`.
- [x] Step 2: Create a highly modular `backend/guardrails/` directory structure.
- [x] Step 3: Implement `backend/guardrails/config.py` (severity mappings & defaults).
- [x] Step 4: Implement `backend/guardrails/validators.py` (regex blocklist, custom words, base64 logic).
- [x] Step 5: Implement `backend/guardrails/input_checks.py` (wiring input filters).
- [x] Step 6: Implement `backend/guardrails/output_checks.py` (wiring output filters).
- [x] Step 7: Implement `backend/guardrails/pipeline.py` (`GuardrailPipeline` orchestrator & error handling).
- [x] Step 8: Implement `backend/guardrails/async_pipeline.py` (asyncio.to_thread wrappers).
- [x] Step 9: Integrate `logger.loki` across the modules for structured logging.
- [x] Step 10: Create `backend/guardrails/demo.py` to test all scenarios.
- [x] Step 11: Integrate the guardrails pipeline in `backend/api.py` before orchestration and before returning the final answer.
- [x] Step 12: Update the frontend error path to render guardrail block messages from the API.

## Files Touched

| File                                   | Action   | What Changed                                                         |
| -------------------------------------- | -------- | -------------------------------------------------------------------- |
| `backend/requirements.txt`             | Modified | Add `guardrails-ai` package requirement                              |
| `backend/guardrails/config.py`         | Created  | Severity mappings and configuration                                  |
| `backend/guardrails/validators.py`     | Created  | Base64, Custom Words, Regex logic                                    |
| `backend/guardrails/input_checks.py`   | Created  | Input filtering assembly                                             |
| `backend/guardrails/output_checks.py`  | Created  | Output filtering assembly                                            |
| `backend/guardrails/async_pipeline.py` | Created  | Async wrapper functions                                              |
| `backend/guardrails/pipeline.py`       | Created  | Main `GuardrailPipeline` class                                       |
| `backend/guardrails/demo.py`           | Created  | Testing script                                                       |
| `backend/guardrails/__init__.py`       | Created  | Exports the main pipeline class                                      |
| `backend/guardrails/models.py`         | Created  | Dataclasses for guardrail issues and results                         |
| `backend/api.py`                       | Modified | Call guardrails before orchestration and before returning the answer |
| `frontend/index.js`                    | Modified | Parse API error JSON and show guardrail block messages               |

## Notes

- We still need to run the `guardrails hub install` commands for the `DetectPII` and `ToxicLanguage` validators if we want the full Guardrails AI checks instead of fallback-only mode.
- The package degrades safely when `guardrails-ai` or hub validators are missing: deterministic checks remain active and the missing dependency is logged as structured metadata.
