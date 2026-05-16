# The Observability Landscape

When building modern applications (especially AI-powered ones), "observability" is broken down into specific pillars. Here is a breakdown of the industry-standard tools available for each functionality.

## Core Observability Tools

| Functionality / Problem to Solve | What it tracks | Industry Standard Tools |
| :--- | :--- | :--- |
| **System & Application Metrics** | Server health (CPU/Memory), API request counts, response latency, custom counters (e.g., "Total LLM Calls"). | **Prometheus + Grafana**, Datadog, New Relic, AWS CloudWatch, Google Cloud Monitoring, AppDynamics, Dynatrace |
| **Centralized Logging** | Aggregating text logs (`logger.info`, `logger.error`) from multiple servers into one search engine to debug runtime issues. | **Grafana Loki**, ELK Stack (Elasticsearch, Logstash, Kibana), Splunk, Datadog Logs, Sumo Logic, Papertrail, AWS CloudWatch Logs |
| **Distributed Tracing** | Tracking a single user request as it travels through multiple microservices (or multiple LangGraph agents) to find bottlenecks. | **Jaeger**, **OpenTelemetry**, Honeycomb, Datadog APM, AWS X-Ray, Lightstep (ServiceNow), Zipkin |
| **Error Tracking & Crash Reporting** | Catching unhandled Python exceptions or frontend crashes and sending alerts with stack traces. | **Sentry**, Rollbar, Bugsnag, Raygun, Firebase Crashlytics |
| **Infrastructure Monitoring** | Monitoring the health of Kubernetes clusters, Docker containers, and database storage. | **Datadog**, Prometheus, Dynatrace, Sysdig, Zabbix, Nagios, AWS CloudWatch |

## AI / LLM Specific Observability

Traditional observability tools struggle with AI because they don't understand concepts like "Tokens", "Prompts", or "Agent Loops". 

| Functionality / Problem to Solve | What it tracks | Industry Standard Tools |
| :--- | :--- | :--- |
| **LLM Tracing & Output Evaluation** | Seeing exactly what prompt was sent to the LLM, the exact response, latency, and evaluating the quality of the answer. | **LangSmith**, Langfuse, Arize Phoenix, Weave (Weights & Biases), TruEra, Traceloop |
| **LLM Gateway & Cost Tracking** | Acting as a proxy between your app and OpenAI to track costs per user/agent, cache responses, and handle rate limits. | **Helicone**, Portkey, LiteLLM, Pezzo |

> [!TIP]
> **OpenTelemetry (OTel)** is not a backend tool itself, but rather the modern **industry standard pipeline**. Instead of writing code specifically for Datadog or Prometheus, you write your code using OpenTelemetry (like we did in `prometheus.py`), and OpenTelemetry translates and sends that data to *any* of the tools listed above.
