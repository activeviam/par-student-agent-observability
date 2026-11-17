"""OpenTelemetry setup sending the traces, metrics and logs of the Python application to the local stack.

The Atoti server is a subprocess: it inherits the ``OTEL_*`` environment variables set here,
so its OpenTelemetry Java agent (added by ``atoti_observability``) exports to the same collector.
"""

from __future__ import annotations

import logging
import os
from typing import Final

from opentelemetry import metrics, trace
from opentelemetry._logs import get_logger_provider, set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Defaults matching `docker-compose.yml`: the OpenTelemetry Collector listens for OTLP over HTTP on port 4318.
# Each one can be overridden by setting the environment variable before starting the application.
_DEFAULT_ENVIRONMENT: Final = {
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
    "OTEL_SERVICE_NAME": "atoti-sample",
    # Export metrics every 10 s instead of every minute so that dashboards react quickly.
    "OTEL_METRIC_EXPORT_INTERVAL": "10000",
}


def setup_telemetry() -> None:
    for name, value in _DEFAULT_ENVIRONMENT.items():
        os.environ.setdefault(name, value)

    # Reads `OTEL_SERVICE_NAME` and `OTEL_RESOURCE_ATTRIBUTES`.
    resource = Resource.create()

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    metrics.set_meter_provider(
        MeterProvider(
            resource=resource,
            metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())],
        )
    )

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    set_logger_provider(logger_provider)

    # Exports the records of Python's `logging` and prints them with their trace and span IDs.
    LoggingInstrumentor().instrument(set_logging_format=True, log_level=logging.INFO)
    # One record per HTTP call between the SDK and the server is noise: the traces already show these calls.
    for noisy_logger_name in ("httpx2", "py4j"):
        logging.getLogger(noisy_logger_name).setLevel(logging.WARNING)


def shutdown_telemetry() -> None:
    """Flush what is still buffered before the process exits."""
    for provider in (
        trace.get_tracer_provider(),
        metrics.get_meter_provider(),
        get_logger_provider(),
    ):
        shutdown = getattr(provider, "shutdown", None)
        if shutdown is not None:
            shutdown()
