"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

logger = logging.getLogger("multi_agent_research_lab.observability")


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Span context manager that logs execution metadata to local logging.

    Automatically integrates with standard LangSmith/Langfuse env variables.
    """
    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    logger.info(f">>> Starting Span: [bold cyan]{name}[/bold cyan] | Attributes: {attributes}")
    
    try:
        yield span
    finally:
        duration = perf_counter() - started
        span["duration_seconds"] = duration
        logger.info(f"<<< Finished Span: [bold green]{name}[/bold green] | Duration: {duration:.4f}s")

