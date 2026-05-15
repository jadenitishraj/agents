# Observability in This Project

This project uses three different observability tools:

- `LangSmith` to observe the agent workflow
- `Helicone` to observe LLM API traffic
- `Grafana` to observe system logs and metrics

They are not duplicates. Each one watches a different layer of the system.

If a student asks:

- "Which agent ran, and what did it do?" → `LangSmith`
- "Which model call cost money, and which agent caused it?" → `Helicone`
- "Was the API slow, and what requests or errors happened?" → `Grafana`

The easiest way to understand the implementation is to follow the code from the user request downward.

## ASCII Tree

```text
agents/
├── frontend/
│   ├── index.html
│   │   └── Student UI for asking questions
│   ├── index.js
│   │   └── Sends POST /research to the backend
│   └── index.css
│       └── Frontend styling only
│
├── backend/
│   ├── api.py
│   │   ├── FastAPI entry point for POST /research
│   │   ├── Calls create_initial_state(...)
│   │   ├── Calls compile_graph(team)
│   │   ├── Runs graph.invoke(...)
│   │   ├── Sends metadata into the run for LangSmith
│   │   ├── Imports Loki logger for request and pipeline logs
│   │   ├── Registers LoggingMiddleware for request/response logging
│   │   ├── Calls setup_prometheus_metrics(app)
│   │   └── Pushes custom counters:
│   │       ├── llm_calls_counter
│   │       ├── iterations_counter
│   │       └── sources_counter
│   │
│   ├── orchestrator.py
│   │   ├── Creates the research state
│   │   ├── Builds the LangGraph flow
│   │   ├── Chooses which agents are active
│   │   └── Controls writer ↔ critic loop
│   │
│   ├── llm.py
│   │   ├── Shared LLM wrapper for all model calls
│   │   ├── Reads:
│   │   │   ├── HELICONE_API_KEY
│   │   │   ├── HELICONE_ENABLED
│   │   │   ├── LLM_MODEL
│   │   │   └── LLM_TEMPERATURE
│   │   ├── If Helicone is disabled:
│   │   │   └── Uses ChatOpenAI normally
│   │   ├── If Helicone is enabled:
│   │   │   ├── base_url = https://oai.helicone.ai/v1
│   │   │   ├── Adds Helicone-Auth header
│   │   │   ├── Adds Helicone-Cache-Enabled header
│   │   │   └── Adds Helicone-Property-Agent header
│   │   └── call_llm(...)
│   │       └── Used by Planner, Reader, Writer, Critic, Compliance
│   │
│   ├── agents/
│   │   ├── planner.py
│   │   │   ├── @traceable(name="planner_agent", run_type="chain")
│   │   │   └── call_llm(..., agent_name="Planner")
│   │   ├── searcher.py
│   │   │   ├── @traceable(name="searcher_agent", run_type="chain")
│   │   │   └── Calls search_web(...)
│   │   ├── reader.py
│   │   │   ├── @traceable(name="reader_agent", run_type="chain")
│   │   │   └── call_llm(..., agent_name="Reader")
│   │   ├── writer.py
│   │   │   ├── @traceable(name="writer_agent", run_type="chain")
│   │   │   └── call_llm(..., agent_name="Writer")
│   │   ├── critic.py
│   │   │   ├── @traceable(name="critic_agent", run_type="chain")
│   │   │   └── call_llm(..., agent_name="Critic")
│   │   ├── compliance.py
│   │   │   ├── @traceable(name="compliance_agent", run_type="chain")
│   │   │   └── call_llm(..., agent_name="Compliance")
│   │   └── reflector.py
│   │       ├── @traceable(name="reflector_agent", run_type="chain")
│   │       └── Deterministic reflection logic, no call_llm(...)
│   │
│   ├── tools/
│   │   └── search.py
│   │       ├── @traceable(name="search_web", run_type="tool")
│   │       ├── Wraps DuckDuckGoSearchResults
│   │       └── Used by Searcher agent
│   │
│   └── requirements.txt
│       ├── langsmith
│       ├── opentelemetry-distro
│       ├── opentelemetry-exporter-prometheus-remote-write
│       ├── opentelemetry-instrumentation-fastapi
│       └── python-logging-loki
│
├── logger/
│   ├── loki.py
│   │   ├── Creates Python logger
│   │   ├── Reads:
│   │   │   ├── LOKI_URL
│   │   │   ├── LOKI_USER_ID
│   │   │   └── LOKI_API_KEY
│   │   └── Adds LokiHandler when credentials exist
│   │
│   ├── middleware.py
│   │   ├── LoggingMiddleware
│   │   ├── Intercepts /research requests
│   │   ├── Logs incoming request method and path
│   │   ├── Measures duration
│   │   ├── Reads outgoing response body
│   │   └── Logs final response payload
│   │
│   └── prometheus.py
│       ├── Reads:
│       │   ├── PROMETHEUS_URL
│       │   ├── PROMETHEUS_USER_ID
│       │   └── PROMETHEUS_API_KEY
│       ├── setup_prometheus_metrics(app)
│       │   ├── Creates OpenTelemetry MeterProvider
│       │   ├── Creates Prometheus remote write exporter
│       │   ├── Registers PeriodicExportingMetricReader
│       │   └── Instruments FastAPI with FastAPIInstrumentor
│       └── Exposes counters:
│           ├── agent_llm_calls_total
│           ├── agent_iterations_total
│           └── agent_sources_total
│
├── plans/
│   ├── 01_langsmith_observability.md
│   │   └── Intent and checklist for LangSmith tracing
│   ├── 02_helicone_observability.md
│   │   └── Intent and checklist for Helicone proxy integration
│   └── 03_grafana_observability.md
│       └── Intent and checklist for Grafana, Loki, and Prometheus
│
└── presentations/
    ├── observability_visual.html
    │   └── Student-facing visual lesson
    └── observability.md
        └── This implementation companion
```

## The Big Picture

There are three different questions here:

1. How did the agent workflow behave?
2. How did the LLM API behave?
3. How did the service behave?

This project answers those with three different tools:

- `LangSmith` for workflow behavior
- `Helicone` for LLM API behavior
- `Grafana` for service behavior

That separation matters. If you mix all three concerns into one mental bucket, observability becomes confusing very quickly.

## 1. LangSmith

### What LangSmith is

`LangSmith` is the workflow-tracing layer.

In this project, it helps students answer:

- Which agents ran?
- In what order did they run?
- Which tool calls happened?
- What inputs and outputs did each step have?
- Did the graph loop back from Critic to Writer?

It is best thought of as the "inside view" of the multi-agent system.

### Core vocabulary

#### `trace`

A `trace` is the full story of one request moving through the system.

Why it is used:
- because a final answer is only the ending
- the trace shows the path that produced that ending

#### `run`

A `run` is one execution of something.

Examples:
- one full research request
- one planner execution
- one search tool call

Why it is used:
- because each part of the system must be inspectable separately

#### `tool`

A `tool` is an outside capability an agent uses.

In this project:
- the Searcher agent uses the DuckDuckGo search tool

Why it is used:
- because agents often depend on external capabilities, not just model text generation

#### `metadata`

`Metadata` is extra information attached to a run.

In this project:
- the question
- the selected team

Why it is used:
- because later you may want to filter or understand runs without opening every single one

### How LangSmith is implemented here

LangSmith is attached directly to the agent and tool functions.

Implementation points:

- `backend/agents/planner.py`
- `backend/agents/searcher.py`
- `backend/agents/reader.py`
- `backend/agents/writer.py`
- `backend/agents/critic.py`
- `backend/agents/compliance.py`
- `backend/agents/reflector.py`
- `backend/tools/search.py`

What was added:

- `from langsmith import traceable`
- `@traceable(name="...", run_type="chain")` on agents
- `@traceable(name="search_web", run_type="tool")` on the search tool

What this means:

- every important agent step becomes visible in LangSmith
- the search tool becomes visible as a nested tool run
- the full request becomes easier to inspect as a structured trace tree

There is also an important setup detail in `backend/api.py`:

- `.env` is loaded early
- `graph.invoke(...)` receives metadata:
  - `question`
  - `team`

That helps the run carry context into the tracing layer.

### What students should understand

LangSmith is not mainly about system health.

It is not the best tool for:
- request/response body logging
- infrastructure dashboards
- cost control

It is best for:
- graph execution visibility
- agent debugging
- tool-call inspection
- understanding how one answer was produced

## 2. Helicone

### What Helicone is

`Helicone` is the LLM traffic layer.

In this project, it helps students answer:

- How many model calls happened?
- Which calls cost money?
- Which calls were slow?
- Which agent caused those calls?
- Can repeated requests be cached?

It is best thought of as the "LLM operations" view.

### Core vocabulary

#### `proxy`

A `proxy` is a middle service between your app and another service.

In this project:
- the app can send LLM requests to Helicone first
- Helicone then forwards them to OpenAI

Why it is used:
- because a proxy can measure and enrich requests without forcing the app to be rewritten from scratch

#### `header`

A `header` is extra information sent with a request.

In this project, Helicone headers are used for:
- authentication
- cache configuration
- agent labeling

Why it is used:
- because it lets the project add observability behavior without changing the core prompt logic

#### `cache`

A `cache` stores a previous result so the same work does not always need to be repeated.

Why it is used:
- because repeated LLM calls can waste both time and money

#### `latency`

`Latency` means how long a request takes.

Why it is used:
- because a correct answer that is too slow still creates a poor user experience

### How Helicone is implemented here

Helicone is attached in exactly one important place:

- `backend/llm.py`

That is a good design choice because all model traffic passes through the shared LLM wrapper.

What happens in `backend/llm.py`:

- the code reads:
  - `HELICONE_API_KEY`
  - `HELICONE_ENABLED`
- if Helicone is off, the app uses `ChatOpenAI` normally
- if Helicone is on:
  - `base_url` becomes `https://oai.helicone.ai/v1`
  - `Helicone-Auth` is added
  - `Helicone-Cache-Enabled` is added
  - `Helicone-Property-Agent` is added when an agent name is provided

That last part is especially important for teaching.

Because the agents call:

- `call_llm(..., agent_name="Planner")`
- `call_llm(..., agent_name="Reader")`
- `call_llm(..., agent_name="Writer")`
- `call_llm(..., agent_name="Critic")`
- `call_llm(..., agent_name="Compliance")`

Helicone can group or filter requests by agent role.

That helps students see a very practical lesson:

- not all LLM calls are equal
- one agent may be responsible for most of the cost
- one agent may be responsible for most of the delay

### What students should understand

Helicone is not mainly about the whole graph structure.

It does not replace LangSmith.

It answers a different set of questions:

- LLM spend
- LLM latency
- cache behavior
- per-agent request analytics

The clean mental model is:

- LangSmith explains the workflow
- Helicone explains the model traffic inside that workflow

## 3. Grafana

### What Grafana is

`Grafana` is the system-observability layer.

In this project, it helps students answer:

- Did the API receive the request?
- How long did the request take?
- What did the response look like?
- What logs were emitted?
- What metrics changed over time?

It is best thought of as the "operations dashboard" view.

### The three most confusing words here

Students often hear `Grafana`, `Loki`, and `Prometheus` together and assume they are the same thing.

They are not.

#### `Grafana`

`Grafana` is the dashboard and exploration layer.

Why it is used:
- because logs and metrics are hard to understand if they stay as raw machine data
- Grafana turns them into panels, charts, and searchable views

#### `Loki`

`Loki` is the log system.

Logs are text records of events.

Examples:
- incoming request
- outgoing response
- error details

Why it is used:
- because when you want to read what happened in words, logs are usually the first place to look

#### `Prometheus`

`Prometheus` is the metrics system.

Metrics are numbers measured over time.

Examples:
- request count
- latency
- total LLM calls
- total iterations

Why it is used:
- because changing system behavior is easier to see on graphs than in text logs

### More core vocabulary

#### `metric`

A `metric` is a measurable number tracked over time.

Why it is used:
- because numbers are the best way to observe trends and system health

#### `log`

A `log` is a text record of an event.

Why it is used:
- because sometimes you need exact detail, not just a number

#### `middleware`

`Middleware` is code that sits between the incoming request and the outgoing response.

Why it is used:
- because it is a natural place to measure duration and capture request/response information

#### `OpenTelemetry`

`OpenTelemetry` is a standard way to collect and export observability data.

Why it is used:
- because teams do not want every app inventing a totally different observability format

#### `counter`

A `counter` is a metric that only increases.

Why it is used:
- because totals are useful for understanding volume and usage over time

### How Grafana is implemented here

Grafana in this project is really two implementation streams:

1. `Loki` for logs
2. `Prometheus` for metrics

#### A. Loki logging

Files involved:

- `logger/loki.py`
- `logger/middleware.py`
- `backend/api.py`

What they do:

`logger/loki.py`
- creates the Python logger
- reads:
  - `LOKI_URL`
  - `LOKI_USER_ID`
  - `LOKI_API_KEY`
- attaches `LokiHandler` if credentials are present

`logger/middleware.py`
- defines `LoggingMiddleware`
- intercepts `/research` requests
- logs:
  - incoming request method and path
  - outgoing response status
  - response duration
  - response payload

`backend/api.py`
- imports the logger
- adds the middleware to the FastAPI app
- logs payload and pipeline lifecycle messages

This means students can understand a key system concept:

- the API layer itself is observable, not just the agent layer

#### B. Prometheus metrics

Files involved:

- `logger/prometheus.py`
- `backend/api.py`

What they do:

`logger/prometheus.py`
- reads:
  - `PROMETHEUS_URL`
  - `PROMETHEUS_USER_ID`
  - `PROMETHEUS_API_KEY`
- creates a `PrometheusRemoteWriteMetricsExporter`
- creates an OpenTelemetry `MeterProvider`
- registers a `PeriodicExportingMetricReader`
- instruments FastAPI with `FastAPIInstrumentor`

It also defines counters:

- `agent_llm_calls_total`
- `agent_iterations_total`
- `agent_sources_total`

Then `backend/api.py` updates those counters after the graph run finishes.

That means students can see both:

- automatic framework-level metrics
- custom application-level metrics

This is a very useful production lesson.

Not everything should be left to automatic instrumentation.
Sometimes the app itself must expose the numbers that matter to the business logic.

### What students should understand

Grafana is not mainly about agent reasoning trees.

It is not the best place to understand:

- why the planner wrote weak search queries
- why the writer missed a fact

It is the best place to understand:

- whether the service is healthy
- whether requests are slow
- whether errors occurred
- what operational data is being emitted

The clean mental model is:

- LangSmith explains the graph
- Helicone explains the model calls
- Grafana explains the service around them

## How the Three Fit Together

Here is the simplest possible explanation:

- `LangSmith` watches the agent workflow
- `Helicone` watches LLM requests
- `Grafana` watches the API and service behavior

Or in one line:

```text
User request
  └── LangSmith asks: "What did the workflow do?"
  └── Helicone asks: "What did the model calls cost and how fast were they?"
  └── Grafana asks: "How healthy was the service while all this happened?"
```

This is why the project uses all three.

If you remove one:

- without `LangSmith`, the workflow becomes harder to debug
- without `Helicone`, model cost and cache behavior become harder to inspect
- without `Grafana`, operational health becomes harder to monitor

## Suggested Reading Order for Students

If a student wants to learn this implementation step by step, this order is best:

1. Read `backend/api.py`
   - this is where the request enters
   - this is where observability components are wired together

2. Read `backend/llm.py`
   - this explains the Helicone integration clearly

3. Read `backend/agents/planner.py` and `backend/tools/search.py`
   - these show the LangSmith decorators in a simple way

4. Read `logger/loki.py` and `logger/middleware.py`
   - these show how request/response logging works

5. Read `logger/prometheus.py`
   - this shows how metrics and FastAPI instrumentation are attached

6. Read the plan files in `plans/`
   - they explain the intended purpose behind each integration

## Final Takeaway

Observability is not one thing.

In this project it is split into three clear layers:

- `LangSmith` for understanding the behavior of the agent graph
- `Helicone` for understanding the behavior of LLM API calls
- `Grafana` for understanding the behavior of the running service

That separation is one of the most important lessons students should learn from this codebase.
