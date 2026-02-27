"""Configuration for the Optic SDK."""

from dataclasses import dataclass, field
from typing import List, Optional
import os


@dataclass
class OpticConfig:
    """Configuration for Optic SDK initialization.

    Attributes:
        api_key: Team API key for authentication. Required.
        service_name: Name of the service being instrumented. Required.
        endpoint: OTLP endpoint URL. Defaults to http://localhost:8080.
        environment: Deployment environment (e.g. production, staging).
        service_version: Version of the service.
        auto_instrument: Whether to auto-detect and instrument libraries.
        enable_traces: Whether to collect traces.
        enable_metrics: Whether to collect metrics.
        enable_logs: Whether to collect logs.
        enable_system_metrics: Whether to collect CPU/memory/disk metrics.
        system_metrics_interval_sec: How often to collect system metrics.
        export_interval_ms: How often to export metrics (milliseconds).
        log_level: Minimum log level to capture (DEBUG, INFO, WARNING, ERROR).
        excluded_urls: URL patterns to exclude from tracing.
    """

    api_key: str = ""
    service_name: str = ""
    endpoint: str = "http://localhost:8080"
    environment: str = "local"
    service_version: str = ""
    auto_instrument: bool = True
    enable_traces: bool = True
    enable_metrics: bool = True
    enable_logs: bool = True
    enable_system_metrics: bool = True
    system_metrics_interval_sec: float = 15.0
    export_interval_ms: int = 10000
    log_level: str = "INFO"
    excluded_urls: List[str] = field(default_factory=list)

    @classmethod
    def from_env(cls, **overrides) -> "OpticConfig":
        """Create config from environment variables with optional overrides."""
        cfg = cls(
            api_key=os.getenv("OPTIC_API_KEY", os.getenv("OTEL_API_KEY", "")),
            service_name=os.getenv("OPTIC_SERVICE_NAME", os.getenv("OTEL_SERVICE_NAME", "")),
            endpoint=os.getenv(
                "OPTIC_ENDPOINT",
                os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:8080"),
            ),
            environment=os.getenv("OPTIC_ENVIRONMENT", "local"),
            service_version=os.getenv("OPTIC_SERVICE_VERSION", ""),
        )
        for key, value in overrides.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
        return cfg
