"""
Client for handling x402 payment challenges and retrying requests
"""

import json
import httpx
from typing import Optional, Dict, Any
from fastx402.types import PaymentChallenge


class X402Client:
    """
    Client for making requests to x402-protected endpoints
    
    Handles 402 responses, triggers frontend payment signing,
    and retries requests with X-PAYMENT headers.
    """
    
    def __init__(
        self,
        base_url: str,
        wallet_provider: str = "instant",
        timeout: float = 30.0
    ):
        """
        Initialize x402 client
        
        Args:
            base_url: Base URL for API
            wallet_provider: "instant" (frontend RPC) or "embedded" (WAAS)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.wallet_provider = wallet_provider
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def _handle_402(
        self,
        challenge: PaymentChallenge,
        original_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle 402 challenge by triggering frontend payment
        
        In instant mode, this would emit an RPC event to the frontend
        to sign the payment. For now, we return the challenge.
        
        Args:
            challenge: Payment challenge
            original_url: Original request URL
            
        Returns:
            Payment data with signature, or None
        """
        # In a real implementation, this would:
        # 1. Emit JSON-RPC event to frontend
        # 2. Wait for frontend to sign payment
        # 3. Return signed payment data
        
        # For now, return None to indicate payment needed
        return None
    
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
        """Close HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

