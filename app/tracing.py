"""
OpenTelemetry Tracing Configuration for SarfX
Provides distributed tracing for Flask app, HTTP requests, and MongoDB operations.
"""

import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

logger = logging.getLogger(__name__)


def setup_tracing(app=None):
    """
    Initialize OpenTelemetry tracing for SarfX application.

    Sets up:
    - OTLP exporter to AI Toolkit trace viewer (localhost:4318)
    - Flask instrumentation for HTTP request tracing
    - Requests instrumentation for outgoing HTTP calls
    - PyMongo instrumentation for database operations
    """

    # Check if tracing is enabled (default: enabled in development)
    tracing_enabled = os.environ.get("TRACING_ENABLED", "true").lower() == "true"

    if not tracing_enabled:
        logger.info("Tracing is disabled")
        return

    try:
        # Configure resource with service information
        resource = Resource.create({
            SERVICE_NAME: os.environ.get("OTEL_SERVICE_NAME", "sarfx-fintech"),
            SERVICE_VERSION: os.environ.get("OTEL_SERVICE_VERSION", "1.0.0"),
            "deployment.environment": os.environ.get("FLASK_ENV", "development")
        })

        # Create TracerProvider with resource
        provider = TracerProvider(resource=resource)

        # Configure OTLP exporter (AI Toolkit default endpoint)
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{otlp_endpoint}/v1/traces"
        )

        # Add BatchSpanProcessor for efficient span export
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)

        # Set the global TracerProvider
        trace.set_tracer_provider(provider)

        # Instrument Flask if app is provided
        if app is not None:
            try:
                from opentelemetry.instrumentation.flask import FlaskInstrumentor
                FlaskInstrumentor().instrument_app(app)
                logger.info("✅ Flask instrumentation enabled")
            except Exception as e:
                logger.warning(f"Failed to instrument Flask: {e}")

        # Instrument requests library for outgoing HTTP calls
        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor
            RequestsInstrumentor().instrument()
            logger.info("✅ Requests instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument requests: {e}")

        # Instrument PyMongo for database operations
        try:
            from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
            PymongoInstrumentor().instrument()
            logger.info("✅ PyMongo instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument PyMongo: {e}")

        logger.info(f"🔍 OpenTelemetry tracing initialized - exporting to {otlp_endpoint}")

    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")


def get_tracer(name: str = "sarfx"):
    """
    Get a tracer instance for custom span creation.

    Args:
        name: Name of the tracer (usually module name)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)
