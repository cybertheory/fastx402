"""
Global configuration for client-side WAAS providers
"""

from typing import Optional
from fastx402.client.waas.base import WAASProvider

# Global WAAS provider instance
_global_waas_provider: Optional[WAASProvider] = None


def set_waas_provider(provider: WAASProvider) -> None:
    """Set the global WAAS provider"""
    global _global_waas_provider
    _global_waas_provider = provider


def get_waas_provider() -> Optional[WAASProvider]:
    """Get the global WAAS provider"""
    return _global_waas_provider


def clear_waas_provider() -> None:
    """Clear the global WAAS provider"""
    global _global_waas_provider
    _global_waas_provider = None


