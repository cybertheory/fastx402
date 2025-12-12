"""
Wrapper for fastmcp clients to handle x402 payment challenges
Similar to httpx_wrapper.py - catches 402 responses and fires callbacks
"""

import json
from typing import Callable, Dict, Any, Optional, Union
import httpx
from fastx402.httpx_wrapper import X402HttpxClient


def wrap_fastmcp_client(
    handle_x402: Callable[[Dict[str, Any]], Union[str, Any]],
    mcp_client=None,
    **httpx_kwargs
):
    """
    Wrap a fastmcp client to automatically handle 402 payment challenges
    
    Catches 402 responses and fires the callback to get payment signature,
    then retries with X-PAYMENT header.
    
    Args:
        handle_x402: Callback function that receives challenge dict and returns signed payment
        mcp_client: Optional existing fastmcp client to wrap (creates new if None)
        **httpx_kwargs: Additional arguments passed to underlying httpx client
        
    Returns:
        Wrapped fastmcp client with x402 support
        
    Example:
        from fastmcp import Client as FastMCPClient
        from fastx402 import wrap_fastmcp_client
        
        async def handle_x402(challenge):
            return await sign_payment(challenge)
        
        # Wrap the fastmcp client
        mcp_client = wrap_fastmcp_client(
            handle_x402=handle_x402,
            mcp_client=FastMCPClient("https://api.example.com/mcp")
        )
        
        async with mcp_client as client:
            result = await client.call_tool("tool_name", {"param": "value"})
    """
    try:
        from fastmcp import Client as FastMCPClient
    except ImportError:
        raise ImportError(
            "fastmcp is not installed. Install it with: pip install fastmcp"
        )
    
    if mcp_client is None:
        raise ValueError("mcp_client must be provided")
    
    # FastMCP clients typically use httpx internally
    # Wrap the underlying httpx client to handle 402 responses
    if hasattr(mcp_client, 'client'):
        # Wrap the underlying httpx client
        wrapped_httpx = X402HttpxClient(
            handle_x402=handle_x402,
            client=mcp_client.client,
            **httpx_kwargs
        )
        mcp_client.client = wrapped_httpx.client
    elif hasattr(mcp_client, '_client'):
        # Alternative attribute name
        wrapped_httpx = X402HttpxClient(
            handle_x402=handle_x402,
            client=mcp_client._client,
            **httpx_kwargs
        )
        mcp_client._client = wrapped_httpx.client
    elif hasattr(mcp_client, '_transport'):
        # If client is accessed via transport, try to wrap at transport level
        # This is a fallback approach
        wrapped_httpx = X402HttpxClient(
            handle_x402=handle_x402,
            **httpx_kwargs
        )
        # Try to inject wrapped client if possible
        if hasattr(mcp_client, '__dict__'):
            mcp_client.__dict__['_x402_wrapped_client'] = wrapped_httpx.client
    
    return mcp_client


class X402FastMCPClient:
    """
    FastMCP client wrapper with built-in x402 support
    
    Catches 402 responses and fires callback to get payment signature,
    then retries with X-PAYMENT header.
    """
    
    def __init__(
        self,
        url: str,
        handle_x402: Callable[[Dict[str, Any]], Union[str, Any]],
        **mcp_client_kwargs
    ):
        """
        Initialize x402-enabled FastMCP client
        
        Args:
            url: MCP server URL
            handle_x402: Callback function for handling payment challenges
            **mcp_client_kwargs: Additional arguments passed to FastMCPClient
        """
        try:
            from fastmcp import Client as FastMCPClient
        except ImportError:
            raise ImportError(
                "fastmcp is not installed. Install it with: pip install fastmcp"
            )
        
        self.handle_x402 = handle_x402
        self._mcp_client = FastMCPClient(url, **mcp_client_kwargs)
        
        # Wrap the underlying httpx client if accessible
        if hasattr(self._mcp_client, 'client'):
            wrapped_httpx = X402HttpxClient(
                handle_x402=handle_x402,
                client=self._mcp_client.client
            )
            self._mcp_client.client = wrapped_httpx.client
        elif hasattr(self._mcp_client, '_client'):
            wrapped_httpx = X402HttpxClient(
                handle_x402=handle_x402,
                client=self._mcp_client._client
            )
            self._mcp_client._client = wrapped_httpx.client
    
    def __getattr__(self, name):
        """Delegate attribute access to underlying MCP client"""
        return getattr(self._mcp_client, name)
    
    def __enter__(self):
        """Context manager entry"""
        return self._mcp_client.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        return self._mcp_client.__exit__(exc_type, exc_val, exc_tb)
    
    async def __aenter__(self):
        """Async context manager entry"""
        return await self._mcp_client.__aenter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        return await self._mcp_client.__aexit__(exc_type, exc_val, exc_tb)

