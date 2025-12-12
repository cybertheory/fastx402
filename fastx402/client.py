"""
Client for handling x402 payment challenges and retrying requests
"""

import json
import httpx
from typing import Optional, Dict, Any, Callable, Awaitable
from fastx402.types import PaymentChallenge, PaymentSignature


class X402Client:
    """
    Client for making requests to x402-protected endpoints
    
    Handles 402 responses, triggers frontend payment signing via RPC,
    and retries requests with X-PAYMENT headers.
    """
    
    def __init__(
        self,
        base_url: str,
        rpc_handler: Optional[Callable[[PaymentChallenge], Awaitable[Optional[PaymentSignature]]]] = None,
        ws_port: Optional[int] = None,
        ws_path: str = "/x402/ws",
        mode: str = "instant",
        timeout: float = 30.0
    ):
        """
        Initialize x402 client
        
        Args:
            base_url: Base URL for API
            rpc_handler: Optional callback function for handling payment challenges (for local signing)
            ws_port: Port for WebSocket server (e.g., 4021). If provided, starts a WebSocket server
                     that frontend x402instant clients can connect to.
            ws_path: WebSocket path (default: "/x402/ws")
            mode: "instant" (user wallet) or "embedded" (WAAS provider)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.rpc_handler = rpc_handler
        self.ws_port = ws_port
        self.ws_path = ws_path
        self.mode = mode
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.ws_server = None
        
        if not self.rpc_handler and not self.ws_port:
            raise ValueError("Either rpc_handler (for local signing) or ws_port (for frontend connection) must be provided")
    
    def set_rpc_handler(self, handler: Callable[[PaymentChallenge], Awaitable[Optional[PaymentSignature]]]) -> None:
        """Set RPC handler callback for payment signing (for local signing)"""
        self.rpc_handler = handler
        self.ws_port = None
    
    def set_ws_server(self, port: int, path: str = "/x402/ws") -> None:
        """Set WebSocket server port (frontend x402instant connects to us)"""
        self.ws_port = port
        self.ws_path = path
        self.rpc_handler = None
    
    async def _handle_402(
        self,
        challenge: PaymentChallenge,
        original_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle 402 challenge by triggering payment signing
        
        Args:
            challenge: Payment challenge
            original_url: Original request URL
            
        Returns:
            Payment data with signature, or None
        """
        # Try WebSocket server first (frontend x402instant connects to us)
        if self.ws_port:
            signature = await self._request_via_websocket_server(challenge)
            if signature:
                return self._signature_to_dict(signature, challenge)
        
        # Use handler if provided (for local signing)
        if self.rpc_handler:
            signature = await self.rpc_handler(challenge)
            if signature:
                return self._signature_to_dict(signature, challenge)
        
        raise ValueError("No RPC handler or WebSocket server configured")
    
    def _signature_to_dict(
        self,
        signature: PaymentSignature,
        challenge: PaymentChallenge
    ) -> Dict[str, Any]:
        """Convert PaymentSignature to dict format"""
        if hasattr(signature, 'model_dump'):
            return signature.model_dump()
        elif hasattr(signature, 'dict'):
            return signature.dict()
        elif isinstance(signature, dict):
            return signature
        else:
            # Convert PaymentSignature object to dict
            challenge_dict = challenge.model_dump() if hasattr(challenge, 'model_dump') else challenge.dict()
            return {
                "signature": signature.signature,
                "signer": signature.signer,
                "challenge": challenge_dict
            }
    
    async def _request_via_websocket_server(
        self,
        challenge: PaymentChallenge
    ) -> Optional[PaymentSignature]:
        """
        Request payment signature via WebSocket server (frontend connects to us)
        
        Args:
            challenge: Payment challenge
            
        Returns:
            PaymentSignature with signature, or None
        """
        if not self.ws_port:
            raise ValueError("WebSocket server port not configured")
        
        try:
            # Import WebSocket server
            from fastx402.client.ws_server import X402WebSocketServer
            
            # Start server if not already running
            if not self.ws_server or not self.ws_server.is_running():
                self.ws_server = X402WebSocketServer(
                    port=self.ws_port,
                    path=self.ws_path,
                    timeout=self.timeout
                )
                await self.ws_server.start()
            
            # Request signature from connected frontend clients
            signature = await self.ws_server.request_signature(challenge)
            return signature
            
        except Exception as e:
            raise ValueError(f"WebSocket server request failed: {str(e)}")
    
    async def request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with x402 payment handling
        
        Args:
            method: HTTP method
            path: Request path
            **kwargs: Additional httpx request arguments
            
        Returns:
            httpx.Response
        """
        url = f"{self.base_url}{path}"
        
        # Make initial request
        response = await self.client.request(method, url, **kwargs)
        
        # Handle 402 Payment Required
        if response.status_code == 402:
            try:
                data = response.json()
                challenge_dict = data.get("challenge")
                
                if challenge_dict:
                    challenge = PaymentChallenge(**challenge_dict)
                    
                    # Get payment signature (from frontend or WAAS)
                    payment_data = await self._handle_402(challenge, url)
                    
                    if payment_data:
                        # Retry request with X-PAYMENT header
                        headers = kwargs.get("headers", {})
                        if headers is None:
                            headers = {}
                        headers["X-PAYMENT"] = json.dumps(payment_data)
                        kwargs["headers"] = headers
                        
                        return await self.client.request(method, url, **kwargs)
            except Exception as e:
                # Log the error for debugging
                import traceback
                traceback.print_exc()
        
        return response
    
    async def get(self, path: str, **kwargs) -> httpx.Response:
        """GET request with x402 handling"""
        return await self.request("GET", path, **kwargs)
    
    async def post(self, path: str, **kwargs) -> httpx.Response:
        """POST request with x402 handling"""
        return await self.request("POST", path, **kwargs)
    
    async def close(self):
        """Close HTTP client and WebSocket server"""
        await self.client.aclose()
        if self.ws_server:
            await self.ws_server.stop()
            self.ws_server = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

