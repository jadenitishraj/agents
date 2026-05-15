# `logger/prometheus.py` Explained

This file is responsible for setting up metrics export, instrumenting FastAPI, and defining custom counters that the application can update after a research run.

## ASCII Tree of the File

```text
logger/
├── prometheus.py
│   ├── import os
│   │   └── used to read Prometheus credentials from environment variables
│   │
│   ├── from opentelemetry import metrics
│   │   └── OpenTelemetry metrics API
│   │
│   ├── from opentelemetry.exporter.prometheus_remote_write import ...
│   │   └── exporter that pushes metrics to a Prometheus-compatible endpoint
│   │
│   ├── from opentelemetry.sdk.metrics import MeterProvider
│   │   └── provides the metrics provider
│   │
│   ├── from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
│   │   └── periodically ships metrics out
│   │
│   ├── from opentelemetry.sdk.resources import Resource
│   │   └── adds service metadata like service.name
│   │
│   ├── from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
│   │   └── auto-instruments FastAPI
│   │
│   ├── PROM_URL = os.getenv("PROMETHEUS_URL", "")
│   ├── PROM_USER = os.getenv("PROMETHEUS_USER_ID", "")
│   ├── PROM_KEY = os.getenv("PROMETHEUS_API_KEY", "")
│   ├── _provider_set = False
│   │   └── guard to avoid setting the provider more than once
│   │
│   ├── def setup_prometheus_metrics(app)
│   │   ├── if PROM_URL and PROM_USER and PROM_KEY and not _provider_set:
│   │   │   ├── resource = Resource(attributes={"service.name": "research-agents"})
│   │   │   ├── exporter = PrometheusRemoteWriteMetricsExporter(...)
│   │   │   ├── reader = PeriodicExportingMetricReader(exporter, ...)
│   │   │   ├── provider = MeterProvider(resource=resource, metric_readers=[reader])
│   │   │   ├── metrics.set_meter_provider(provider)
│   │   │   └── _provider_set = True
│   │   └── FastAPIInstrumentor.instrument_app(app)
│   │
│   ├── meter = metrics.get_meter("research.agents.meter")
│   │   └── shared meter for defining custom app metrics
│   │
│   ├── llm_calls_counter = meter.create_counter(...)
│   ├── iterations_counter = meter.create_counter(...)
│   └── sources_counter = meter.create_counter(...)
│       └── exported counters used by backend/api.py
```

## What the File Is Doing

This file does two connected jobs:

1. set up metrics export and FastAPI instrumentation
2. define custom counters for project-specific numbers

That combination is important because real observability usually needs both:

- automatic metrics
- custom business metrics

## Important Vocabulary

### `metric`

A `metric` is a number tracked over time.

Examples:
- request count
- latency
- total LLM calls

Why it is used:
- because system trends are easier to understand from changing numbers than from raw text logs

### `Prometheus`

`Prometheus` is a metrics system built for time-series data.

Why it is used:
- because operations teams need graphs and trends, not only event text

### `OpenTelemetry`

`OpenTelemetry` is a standard system for instrumenting and exporting telemetry data.

Why it is used:
- because it gives the app a standard way to produce observability data

### `instrumentation`

`Instrumentation` means adding hooks that let a system produce observability data.

In this file:
- FastAPI is instrumented automatically

Why it is used:
- because the framework can emit useful metrics without every endpoint writing them manually

### `counter`

A `counter` is a metric that only increases.

In this file:
- total LLM calls
- total iterations
- total sources

Why it is used:
- because totals are useful for throughput and usage monitoring

## Why the `_provider_set` Guard Matters

This variable:

```python
_provider_set = False
```

exists so the meter provider is not registered multiple times.

Why this matters:

- repeated setup could create duplicated or conflicting metric configuration
- observability setup code is often imported more than once in development or reload scenarios

So this guard protects the metrics pipeline from repeated initialization.

## Data Flow Inside This File

```text
Environment Variables
  ├── PROMETHEUS_URL
  ├── PROMETHEUS_USER_ID
  └── PROMETHEUS_API_KEY
          │
          ▼
setup_prometheus_metrics(app)
  ├── create Resource(service.name="research-agents")
  ├── create Prometheus remote-write exporter
  ├── create PeriodicExportingMetricReader
  ├── create MeterProvider
  ├── register provider
  └── instrument FastAPI app
          │
          ▼
meter = metrics.get_meter(...)
  ├── create llm_calls_counter
  ├── create iterations_counter
  └── create sources_counter
          │
          ▼
backend/api.py imports counters and increments them
```

## Automatic Metrics vs Custom Metrics

This file teaches a very useful distinction.

### Automatic metrics

These come from:

```python
FastAPIInstrumentor.instrument_app(app)
```

Why they help:

- they can capture framework-level behavior such as request handling metrics
- they reduce manual work

### Custom metrics

These are:

- `agent_llm_calls_total`
- `agent_iterations_total`
- `agent_sources_total`

Why they help:

- the framework does not know your business logic
- only your app knows what an "iteration" or "sources count" means in this research pipeline

That is why custom metrics are necessary.

## What This File Gives Students

This file teaches a strong production lesson:

- good observability is not only about "is the server up?"
- it is also about "what numbers matter for this application?"

This project chooses three application-specific metrics that students can understand immediately:

- how many LLM calls happened
- how many writer/critic iterations happened
- how many sources were gathered

## Where It Gets Used

This file is activated from:

- `backend/api.py`

`backend/api.py` does two things with it:

- calls `setup_prometheus_metrics(app)` during app setup
- imports and increments the counters after the pipeline finishes
