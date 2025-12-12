"""
fastx402 - FastAPI integration for x402 HTTP-native payments
"""

from fastx402.decorators import payment_required, configure_server
from fastx402.server import X402Server
from fastx402.types import PaymentChallenge, PaymentConfig
from fastx402.requests_wrapper import patch_requests, X402Session
from fastx402.httpx_wrapper import X402HttpxClient

# Import X402Client - handle package/module name conflict
# The client.py module and client/ package conflict, so import directly
import importlib.util
import os
_client_path = os.path.join(os.path.dirname(__file__), "client.py")
_spec = importlib.util.spec_from_file_location("fastx402._client_module", _client_path)
_client_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_client_mod)
X402Client = _client_mod.X402Client

# Client-side WAAS providers (from client/waas package)
from fastx402.client.waas import PrivyWAASProvider, WAASProvider
from fastx402.client.waas.signature import sign_payment_challenge
from fastx402.client.waas.config import set_waas_provider, get_waas_provider

# FastAPI server wrapper (optional dependency)
try:
    from fastx402.fastapi_server_wrapper import wrap_fastapi_server, X402FastAPIApp
    _has_fastapi = True
except ImportError:
    _has_fastapi = False
    wrap_fastapi_server = None
    X402FastAPIApp = None

# FastMCP wrappers (optional dependency)
try:
    from fastx402.fastmcp_client_wrapper import wrap_fastmcp_client, X402FastMCPClient
    from fastx402.fastmcp_server_wrapper import wrap_fastmcp_server, X402FastMCPServer
    _has_fastmcp = True
except ImportError:
    _has_fastmcp = False
    wrap_fastmcp_client = None
    X402FastMCPClient = None
    wrap_fastmcp_server = None
    X402FastMCPServer = None

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
    # Client-side WAAS
    "PrivyWAASProvider",
    "WAASProvider",
    "sign_payment_challenge",
    "set_waas_provider",
    "get_waas_provider",
]

# Add optional wrappers if available
if _has_fastapi:
    __all__.extend(["wrap_fastapi_server", "X402FastAPIApp"])

if _has_fastmcp:
    __all__.extend([
        "wrap_fastmcp_client",
        "X402FastMCPClient",
        "wrap_fastmcp_server",
        "X402FastMCPServer",
    ])
