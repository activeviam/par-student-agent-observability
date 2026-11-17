"""Queries of the tutorial, run at startup to produce some traces, metrics and logs."""

from __future__ import annotations

import logging
import time
from typing import Final

import atoti as tt
from opentelemetry import trace
from opentelemetry.metrics import Meter

_LOGGER: Final = logging.getLogger(__name__)
_TRACER: Final = trace.get_tracer(__name__)


def run_sample_queries(cube: tt.Cube, /, *, meter: Meter) -> None:
    l, m = cube.levels, cube.measures
    duration_histogram = meter.create_histogram(
        "atoti_sample.query.duration",
        unit="s",
        description="Duration of the sample queries run from Python.",
    )

    queries = {
        "margin per product": lambda: cube.query(
            m["Margin"], m["Margin rate"], levels=[l["Products", "Product", "Product"]]
        ),
        "average amount per shop": lambda: cube.query(
            m["Average amount per shop"],
            include_totals=True,
            levels=[l["Sub category"]],
        ),
        "percent of parent amount": lambda: cube.query(
            m["Percent of parent amount"], m["Margin rate"], levels=[l["Category"]]
        ),
        "country simulation": lambda: cube.query(
            m["Quantity.SUM"],
            m["Amount.SUM"],
            include_totals=True,
            levels=[l["Country Simulation"], l["Country"]],
        ),
    }

    for name, query in queries.items():
        with _TRACER.start_as_current_span(f"query {name}"):
            start = time.perf_counter()
            result = query()
            duration_histogram.record(
                time.perf_counter() - start, attributes={"query": name}
            )
            _LOGGER.info("Query %r returned %d rows:\n%s", name, len(result), result)
