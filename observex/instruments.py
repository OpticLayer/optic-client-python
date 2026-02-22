"""Auto-detect installed libraries and instrument them."""

import importlib
import logging
from typing import List

logger = logging.getLogger("observex.instruments")

# Map of library → OTel instrumentor class path
INSTRUMENTORS = {
    "flask": "opentelemetry.instrumentation.flask:FlaskInstrumentor",
    "django": "opentelemetry.instrumentation.django:DjangoInstrumentor",
    "fastapi": "opentelemetry.instrumentation.fastapi:FastAPIInstrumentor",
    "requests": "opentelemetry.instrumentation.requests:RequestsInstrumentor",
    "urllib3": "opentelemetry.instrumentation.urllib3:URLLib3Instrumentor",
    "sqlalchemy": "opentelemetry.instrumentation.sqlalchemy:SQLAlchemyInstrumentor",
    "pymysql": "opentelemetry.instrumentation.pymysql:PyMySQLInstrumentor",
    "psycopg2": "opentelemetry.instrumentation.psycopg2:Psycopg2Instrumentor",
    "redis": "opentelemetry.instrumentation.redis:RedisInstrumentor",
    "celery": "opentelemetry.instrumentation.celery:CeleryInstrumentor",
    "httpx": "opentelemetry.instrumentation.httpx:HTTPXClientInstrumentor",
    "aiohttp": "opentelemetry.instrumentation.aiohttp_client:AioHttpClientInstrumentor",
    "kafka": "opentelemetry.instrumentation.kafka:KafkaInstrumentor",
}


def auto_instrument(excluded_urls: List[str] = None) -> None:
    """Detect installed libraries and instrument them automatically.

    Only instruments libraries that are:
    1. Already installed in the environment
    2. Have corresponding OTel instrumentation packages installed
    """
    excluded_urls = excluded_urls or []
    instrumented = []

    for lib_name, instrumentor_path in INSTRUMENTORS.items():
        # Check if the target library is installed
        try:
            importlib.import_module(lib_name)
        except ImportError:
            continue

        # Check if the OTel instrumentor is installed
        module_path, class_name = instrumentor_path.rsplit(":", 1)
        try:
            module = importlib.import_module(module_path)
            instrumentor_cls = getattr(module, class_name)
        except (ImportError, AttributeError):
            logger.debug(f"Instrumentor not available for {lib_name}, skipping")
            continue

        # Instrument it
        try:
            instrumentor = instrumentor_cls()
            if not instrumentor.is_instrumented_by_opentelemetry:
                kwargs = {}
                if excluded_urls and hasattr(instrumentor, "instrument"):
                    kwargs["excluded_urls"] = ",".join(excluded_urls)
                instrumentor.instrument(**kwargs)
                instrumented.append(lib_name)
        except Exception as e:
            logger.warning(f"Failed to instrument {lib_name}: {e}")

    if instrumented:
        logger.info(f"Auto-instrumented: {', '.join(instrumented)}")
