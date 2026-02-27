"""
Optic Python SDK — auto-instrument your application with one line of code.

Usage:
    import optic
    optic.init(api_key="your-key", service_name="my-app")

That's it. Traces, metrics, and logs are automatically collected.
"""

from optic.config import OpticConfig
from optic._core import init, shutdown, is_initialized

__version__ = "0.1.0"
__all__ = ["init", "shutdown", "is_initialized", "OpticConfig"]
