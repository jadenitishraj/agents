# Feature: Grafana Observability (Loki & Prometheus)

**Date:** 2026-05-15
**Status:** 🔲 Planned | 🔄 In Progress | ✅ Complete

## Description

Integrate Grafana Cloud for infrastructure-level observability to complement the existing LangSmith agent-level tracing. This feature will introduce Loki for centralizing text logs (including raw HTTP request/response payloads) and Prometheus (via OpenTelemetry) for tracking API system metrics like latency, throughput, error rates, and hardware utilization. Agent intelligence (e.g., iterations, LLM calls) will remain exclusively in LangSmith to adhere to the project's separation of concerns.

## Checklist

- [x] Step 1: Add Grafana Cloud credentials (`LOKI_URL`, `LOKI_USER_ID`, `LOKI_API_KEY`, `PROMETHEUS_URL`, etc.) to `.env`.
- [x] Step 2: Add required observability packages (`python-logging-loki`, `opentelemetry-distro`, `opentelemetry-exporter-otlp`, `opentelemetry-instrumentation-fastapi`) to `backend/requirements.txt`.
- [x] Step 3: Implement `LokiHandler` in `backend/api.py` to route all standard Python `logger` output to Grafana.
- [x] Step 4: Create a FastAPI Middleware in `backend/api.py` to intercept and log the raw JSON of every incoming Request and outgoing Response to Loki.
- [x] Step 5: Instrument the FastAPI application using OpenTelemetry (`FastAPIInstrumentor`) to automatically track HTTP system metrics (latency, error rates) and push them to Grafana Prometheus.
- [ ] Test 1: Run `python main.py`, submit a research request via the frontend, and verify the JSON payloads appear in Grafana Loki.
- [ ] Test 2: Verify that API latency metrics appear in Grafana Prometheus dashboards.

## Files Touched

> Updated after implementation.

| File | Action | What Changed |
|------|--------|-------------|
| `backend/requirements.txt` | Modified | Added observability dependencies. |
| `backend/api.py` | Modified | Added Loki logger, OpenTelemetry setup, and Request/Response middleware. |

## Notes

- **Separation of Concerns:** LangSmith remains the source of truth for "Agent Intelligence" (traces, token counts, iterations). Grafana handles "Infrastructure Health" (server up/down, API speed, full text logs).
- **No Background Agents:** As per `agents.md` rules, we will not use Docker or local background services. The FastAPI application will directly "push" data to Grafana Cloud over HTTP.
