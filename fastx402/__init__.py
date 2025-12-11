"""
fastx402 - FastAPI integration for x402 HTTP-native payments
"""

from fastx402.decorators import payment_required, configure_server
from fastx402.client import X402Client
from fastx402.server import X402Server
from fastx402.types import PaymentChallenge, PaymentConfig
from fastx402.requests_wrapper import patch_requests, X402Session
from fastx402.httpx_wrapper import X402HttpxClient

__version__ = "0.1.0"
__all__ = [
    "payment_required",
    "configure_server",
    "X402Client",
    "X402Server",
    "PaymentChallenge",
    "PaymentConfig",
    "patch_requests",
    "X402Session",
    "X402HttpxClient",
]

