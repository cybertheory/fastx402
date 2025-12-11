"""
Wallet-as-a-Service (WAAS) provider interfaces
"""

from fastx402.waas.base import WAASProvider
from fastx402.waas.privy import PrivyProvider

__all__ = ["WAASProvider", "PrivyProvider"]

