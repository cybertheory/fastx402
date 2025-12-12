"""
Wrapper for FastAPI servers to enable making x402 requests
FastAPI servers need to be able to make outgoing x402 requests to other services
"""

import inspect
from typing import Optional, Callable, Dict, Any, Union
import httpx
from fastx402.httpx_wrapper import X402HttpxClient


def wrap_fastapi_server(
    app,
    handle_x402: Optional[Callable[[Dict[str, Any]], Union[str, Any]]] = None,
    **httpx_kwargs
):
    """
    Wrap a FastAPI application to enable making x402 requests
    
    Injects x402-enabled HTTP clients so the server can make
    outgoing requests to x402-protected endpoints.
    
    Args:
        app: FastAPI application instance
        handle_x402: Optional callback function for handling payment challenges
                     (if None, server won't handle 402 responses automatically)
        **httpx_kwargs: Additional arguments passed to underlying httpx client
        
    Returns:
        Wrapped FastAPI app with x402 request capability
        
    Example:
        from fastapi import FastAPI
        from fastx402 import wrap_fastapi_server
        
        app = FastAPI()
        
        async def handle_x402(challenge):
            return await sign_payment(challenge)
        
        # Wrap the FastAPI app
        app = wrap_fastapi_server(
            app=app,
            handle_x402=handle_x402
        )
        
        # Now app can make x402 requests using app.state.x402_client
        @app.get("/proxy")
        async def proxy_endpoint():
            client = app.state.x402_client
            response = await client.get("https://api.example.com/paid")
            return await response.json()
    """
    try:
        from fastapi import FastAPI
    except ImportError:
        raise ImportError(
            "fastapi is not installed. Install it with: pip install fastapi"
        )
    
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
        # Just provide a regular httpx client if no handler
        x402_client = httpx.AsyncClient(**httpx_kwargs)
    
    # Attach x402 client to app state for making requests
    if not hasattr(app, 'state'):
        from fastapi import Request
        app.state = type('State', (), {})()
    
    app.state.x402_client = x402_client
    
    return app


class X402FastAPIApp:
    """
    FastAPI application wrapper with built-in x402 request capability
    
    Enables the server to make outgoing x402 requests to other services.
    """
    
    def __init__(
        self,
        app=None,
        handle_x402: Optional[Callable[[Dict[str, Any]], Union[str, Any]]] = None,
        **fastapi_kwargs
    ):
        """
        Initialize x402-enabled FastAPI application
        
        Args:
            app: Optional existing FastAPI app (creates new if None)
            handle_x402: Optional callback function for handling payment challenges
            **fastapi_kwargs: Additional arguments passed to FastAPI if creating new app
        """
        try:
            from fastapi import FastAPI
        except ImportError:
            raise ImportError(
                "fastapi is not installed. Install it with: pip install fastapi"
            )
        
        if app is None:
            app = FastAPI(**fastapi_kwargs)
        
        self.handle_x402 = handle_x402
        self._app = wrap_fastapi_server(
            app=app,
            handle_x402=handle_x402
        )
    
    def __getattr__(self, name):
        """Delegate attribute access to underlying FastAPI app"""
        return getattr(self._app, name)
    
    @property
    def app(self):
        """Get the underlying FastAPI app"""
        return self._app

