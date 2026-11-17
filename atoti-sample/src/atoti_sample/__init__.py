"""Atoti tutorial session sending its telemetry to the local Grafana stack."""

from __future__ import annotations

import logging
import os
from typing import Final

from .telemetry import setup_telemetry, shutdown_telemetry

_LOGGER: Final = logging.getLogger(__name__)


def main() -> None:
    # Must run before starting the session so that the server subprocess inherits the `OTEL_*` variables.
    setup_telemetry()

    try:
        _run()
    except KeyboardInterrupt:
        _LOGGER.info("Stopping.")
    finally:
        shutdown_telemetry()


def _run() -> None:
    # Imported after the telemetry setup so that Atoti uses the configured providers.
    import atoti as tt
    from atoti_observability import ObservabilityConfig
    from opentelemetry import metrics, trace

    from .ai import create_ai_config
    from .data_model import create_data_model
    from .queries import run_sample_queries

    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)

    with tracer.start_as_current_span("atoti-sample startup"):
        with tracer.start_as_current_span("start session"):
            session = tt.Session.start(
                tt.SessionConfig(
                    port=int(os.environ.get("ATOTI_PORT", "9090")),
                    observability=ObservabilityConfig(
                        server_service_name=os.environ.get(
                            "ATOTI_SERVER_SERVICE_NAME", "atoti-sample-server"
                        ),
                    ),
                    ai=create_ai_config(),
                )
            )
        with tracer.start_as_current_span("create data model"):
            cube = create_data_model(session)
        run_sample_queries(cube, meter=meter)

    _LOGGER.info("Session ready at %s (press Ctrl+C to stop).", session.url)
    session.wait()
