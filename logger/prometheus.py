import os
from opentelemetry import metrics
from opentelemetry.exporter.prometheus_remote_write import PrometheusRemoteWriteMetricsExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

PROM_URL = os.getenv("PROMETHEUS_URL", "")
PROM_USER = os.getenv("PROMETHEUS_USER_ID", "")
PROM_KEY = os.getenv("PROMETHEUS_API_KEY", "")

_provider_set = False

def setup_prometheus_metrics(app):
    global _provider_set
    if PROM_URL and PROM_USER and PROM_KEY and not _provider_set:
        resource = Resource(attributes={"service.name": "research-agents"})
        
        exporter = PrometheusRemoteWriteMetricsExporter(
            endpoint=PROM_URL,
            basic_auth={
                "username": PROM_USER,
                "password": PROM_KEY,
            }
        )
        
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)
        _provider_set = True

    # Instrument FastAPI app
    FastAPIInstrumentor.instrument_app(app)

# Export the metrics counters so they can be imported directly
meter = metrics.get_meter("research.agents.meter")
llm_calls_counter = meter.create_counter("agent_llm_calls_total", description="Total LLM calls made by agents")
iterations_counter = meter.create_counter("agent_iterations_total", description="Total writer/critic loops")
sources_counter = meter.create_counter("agent_sources_total", description="Total web sources found")
