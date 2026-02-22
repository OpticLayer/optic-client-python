"""Automatic system metrics collection (CPU, memory, disk, network)."""

import logging
import threading
from typing import Optional

logger = logging.getLogger("observex.system_metrics")

_collector_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


def start_system_metrics(interval_sec: float = 15.0) -> None:
    """Start a background thread that collects system metrics periodically."""
    global _collector_thread

    try:
        import psutil
    except ImportError:
        logger.debug("psutil not installed, system metrics disabled")
        return

    from opentelemetry import metrics

    meter = metrics.get_meter("observex.system", "0.1.0")

    cpu_gauge = meter.create_observable_gauge(
        "system.cpu.utilization",
        description="CPU utilization (0.0 to 1.0)",
        unit="1",
    )
    memory_gauge = meter.create_observable_gauge(
        "system.memory.utilization",
        description="Memory utilization (0.0 to 1.0)",
        unit="1",
    )
    disk_gauge = meter.create_observable_gauge(
        "system.disk.utilization",
        description="Disk utilization (0.0 to 1.0)",
        unit="1",
    )

    def _cpu_callback(_):
        try:
            from opentelemetry.metrics import Observation
            cpu = psutil.cpu_percent(interval=None) / 100.0
            return [Observation(cpu)]
        except Exception:
            return []

    def _memory_callback(_):
        try:
            from opentelemetry.metrics import Observation
            mem = psutil.virtual_memory().percent / 100.0
            return [Observation(mem)]
        except Exception:
            return []

    def _disk_callback(_):
        try:
            from opentelemetry.metrics import Observation
            disk = psutil.disk_usage("/").percent / 100.0
            return [Observation(disk)]
        except Exception:
            return []

    # Re-create gauges with callbacks
    meter.create_observable_gauge(
        "system.cpu.utilization",
        callbacks=[_cpu_callback],
        description="CPU utilization (0.0 to 1.0)",
        unit="1",
    )
    meter.create_observable_gauge(
        "system.memory.utilization",
        callbacks=[_memory_callback],
        description="Memory utilization (0.0 to 1.0)",
        unit="1",
    )
    meter.create_observable_gauge(
        "system.disk.utilization",
        callbacks=[_disk_callback],
        description="Disk utilization (0.0 to 1.0)",
        unit="1",
    )

    logger.info("System metrics collection started")
