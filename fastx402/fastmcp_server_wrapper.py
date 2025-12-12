"""
Wrapper for fastmcp servers to enable making x402 requests
Servers need to be able to make outgoing x402 requests to other services
"""

import inspect
from typing import Optional, Callable, Dict, Any, Union
import httpx
from fastx402.httpx_wrapper import X402HttpxClient


def wrap_fastmcp_server(
    handle_x402: Optional[Callable[[Dict[str, Any]], Union[str, Any]]] = None,
    mcp_server=None,
    **httpx_kwargs
):
    """
    Wrap a fastmcp server to enable making x402 requests
    
    Injects x402-enabled HTTP clients so the server can make
    outgoing requests to x402-protected endpoints.
    
    Args:
        handle_x402: Optional callback function for handling payment challenges
                     (if None, server won't handle 402 responses automatically)
        mcp_server: Optional existing fastmcp server to wrap (creates new if None)
        **httpx_kwargs: Additional arguments passed to underlying httpx client
        
    Returns:
        Wrapped fastmcp server with x402 request capability
        
    Example:
        from fastmcp import Server as FastMCPServer
        from fastx402 import wrap_fastmcp_server
        
        async def handle_x402(challenge):
            return await sign_payment(challenge)
        
        # Wrap the fastmcp server
        server = wrap_fastmcp_server(
            handle_x402=handle_x402,
            mcp_server=FastMCPServer()
        )
        
        # Now server can make x402 requests using server.x402_client
        response = await server.x402_client.get("https://api.example.com/paid")
    """
    try:
        from fastmcp import Server as FastMCPServer
    except ImportError:
        raise ImportError(
            "fastmcp is not installed. Install it with: pip install fastmcp"
        )
    
    if mcp_server is None:
        raise ValueError("mcp_server must be provided")
    
    # Create x402-enabled HTTP client for the server to use
    if handle_x402:
        # Determine if async based on handle_x402
        if inspect.iscoroutinefunction(handle_x402):
            httpx_client = httpx.AsyncClient(**httpx_kwargs)
        else:
            httpx_client = httpx.Client(**httpx_kwargs)
        
        x402_client = X402HttpxClient(
            handle_x402=handle_x402,
            client=httpx_client,
            **httpx_kwargs
        )
    else:
        # Just provide a regular httpx client if no handler (default to async)
        x402_client = httpx.AsyncClient(**httpx_kwargs)
    
    # Attach x402 client to server for making requests
    mcp_server.x402_client = x402_client
    
    # If server has an internal HTTP client, wrap it too
    if hasattr(mcp_server, 'client'):
        if handle_x402:
            wrapped_internal = X402HttpxClient(
                handle_x402=handle_x402,
                client=mcp_server.client,
                **httpx_kwargs
            )
            mcp_server.client = wrapped_internal.client
    elif hasattr(mcp_server, '_client'):
        if handle_x402:
            wrapped_internal = X402HttpxClient(
                handle_x402=handle_x402,
                client=mcp_server._client,
                **httpx_kwargs
            )
            mcp_server._client = wrapped_internal.client
    
    return mcp_server


class X402FastMCPServer:
    """
    FastMCP server wrapper with built-in x402 request capability
    
    Enables the server to make outgoing x402 requests to other services.
    """
    
    def __init__(
        self,
        handle_x402: Optional[Callable[[Dict[str, Any]], Union[str, Any]]] = None,
        **mcp_server_kwargs
    ):
        """
        Initialize x402-enabled FastMCP server
        
        Args:
            handle_x402: Optional callback function for handling payment challenges
            **mcp_server_kwargs: Additional arguments passed to FastMCPServer
        """
        try:
            from fastmcp import Server as FastMCPServer
        except ImportError:
            raise ImportError(
                "fastmcp is not installed. Install it with: pip install fastmcp"
            )
        
        self.handle_x402 = handle_x402
        self._mcp_server = FastMCPServer(**mcp_server_kwargs)
        
        # Create x402-enabled HTTP client for making requests
        if handle_x402:
            if inspect.iscoroutinefunction(handle_x402):
                httpx_client = httpx.AsyncClient()
            else:
                httpx_client = httpx.Client()
            
            self.x402_client = X402HttpxClient(
                handle_x402=handle_x402,
                client=httpx_client
            )
        else:
            # Provide regular httpx client if no handler
            self.x402_client = httpx.AsyncClient()
        
        # Wrap internal HTTP client if it exists
        if hasattr(self._mcp_server, 'client') and handle_x402:
            wrapped_internal = X402HttpxClient(
                handle_x402=handle_x402,
                client=self._mcp_server.client
            )
            self._mcp_server.client = wrapped_internal.client
        elif hasattr(self._mcp_server, '_client') and handle_x402:
            wrapped_internal = X402HttpxClient(
                handle_x402=handle_x402,
                client=self._mcp_server._client
            )
            self._mcp_server._client = wrapped_internal.client
    
    def __getattr__(self, name):
        """Delegate attribute access to underlying MCP server"""
        return getattr(self._mcp_server, name)
    
    def __enter__(self):
        """Context manager entry"""
        return self._mcp_server.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        return self._mcp_server.__exit__(exc_type, exc_val, exc_tb)
    
    async def __aenter__(self):
        """Async context manager entry"""
        return await self._mcp_server.__aenter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        return await self._mcp_server.__aexit__(exc_type, exc_val, exc_tb)

