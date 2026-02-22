"""Core initialization logic — wires up TracerProvider, MeterProvider, LoggerProvider."""

import atexit
import logging
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from observex.config import ObserveXConfig
from observex.instruments import auto_instrument
from observex.system_metrics import start_system_metrics

_initialized = False
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None
_logger_provider: Optional[LoggerProvider] = None


def is_initialized() -> bool:
    """Return whether the SDK has been initialized."""
    return _initialized


def init(
    api_key: str = "",
    service_name: str = "",
    endpoint: str = "",
    **kwargs,
) -> None:
    """Initialize ObserveX SDK — sets up tracing, metrics, and logging.

    This is the only function you need to call. Everything else is automatic.

    Args:
        api_key: Team API key. Can also be set via OBSERVEX_API_KEY env var.
        service_name: Service name. Can also be set via OBSERVEX_SERVICE_NAME.
        endpoint: OTLP endpoint. Defaults to http://localhost:8080.
        **kwargs: Additional ObserveXConfig fields.
    """
    global _initialized, _tracer_provider, _meter_provider, _logger_provider

    if _initialized:
        return

    # Build config from env + explicit args
    overrides = {k: v for k, v in kwargs.items() if v is not None}
    if api_key:
        overrides["api_key"] = api_key
    if service_name:
        overrides["service_name"] = service_name
    if endpoint:
        overrides["endpoint"] = endpoint

    cfg = ObserveXConfig.from_env(**overrides)

    if not cfg.api_key:
        raise ValueError(
            "ObserveX API key is required. Pass api_key= or set OBSERVEX_API_KEY env var."
        )
    if not cfg.service_name:
        raise ValueError(
            "Service name is required. Pass service_name= or set OBSERVEX_SERVICE_NAME env var."
        )

    # Build OTel resource
    resource = Resource.create({
        SERVICE_NAME: cfg.service_name,
        "deployment.environment": cfg.environment,
        "service.version": cfg.service_version or "unknown",
        "telemetry.sdk.name": "observex-sdk",
        "telemetry.sdk.version": "0.1.0",
    })

    headers = {"Authorization": f"Bearer {cfg.api_key}"}

    # ── Traces ────────────────────────────────────────────────────────────────
    if cfg.enable_traces:
        trace_exporter = OTLPSpanExporter(
            endpoint=f"{cfg.endpoint}/otlp/v1/traces",
            headers=headers,
        )
        _tracer_provider = TracerProvider(resource=resource)
        _tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(_tracer_provider)

    # ── Metrics ───────────────────────────────────────────────────────────────
    if cfg.enable_metrics:
        metric_exporter = OTLPMetricExporter(
            endpoint=f"{cfg.endpoint}/otlp/v1/metrics",
            headers=headers,
        )
        reader = PeriodicExportingMetricReader(
            metric_exporter, export_interval_millis=cfg.export_interval_ms
        )
        _meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(_meter_provider)

    # ── Logs ──────────────────────────────────────────────────────────────────
    if cfg.enable_logs:
        log_exporter = OTLPLogExporter(
            endpoint=f"{cfg.endpoint}/otlp/v1/logs",
            headers=headers,
        )
        _logger_provider = LoggerProvider(resource=resource)
        _logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

        # Bridge Python logging → OTel
        log_levels = {"DEBUG": logging.DEBUG, "INFO": logging.INFO,
                      "WARNING": logging.WARNING, "ERROR": logging.ERROR}
        level = log_levels.get(cfg.log_level.upper(), logging.INFO)
        handler = LoggingHandler(level=level, logger_provider=_logger_provider)
        logging.getLogger().addHandler(handler)

    # ── System Metrics ────────────────────────────────────────────────────────
    if cfg.enable_system_metrics and cfg.enable_metrics:
        start_system_metrics(cfg.system_metrics_interval_sec)

    # ── Auto-instrumentation ─────────────────────────────────────────────────
    if cfg.auto_instrument:
        auto_instrument(cfg.excluded_urls)

    _initialized = True
    atexit.register(shutdown)

    logging.getLogger("observex").info(
        f"ObserveX SDK initialized: service={cfg.service_name}, "
        f"endpoint={cfg.endpoint}, traces={cfg.enable_traces}, "
        f"metrics={cfg.enable_metrics}, logs={cfg.enable_logs}"
    )


def shutdown() -> None:
    """Flush and shut down all providers."""
    global _initialized
    if not _initialized:
        return

    if _tracer_provider:
        _tracer_provider.shutdown()
    if _meter_provider:
        _meter_provider.shutdown()
    if _logger_provider:
        _logger_provider.shutdown()

    _initialized = False
