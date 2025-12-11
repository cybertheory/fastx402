"""
Wrapper for httpx library to handle x402 payment challenges
"""

import json
from typing import Callable, Dict, Any, Optional, Union
import httpx
from httpx import AsyncClient, Client


class X402HttpxClient:
    """
    httpx client wrapper with x402 payment challenge handling
    
    Supports both sync and async clients
    """
    
    def __init__(
        self,
        handle_x402: Callable[[Dict[str, Any]], Union[str, Any]],
        client: Optional[Union[Client, AsyncClient]] = None,
        **kwargs
    ):
        """
        Initialize x402-enabled httpx client
        
        Args:
            handle_x402: Callback function that receives challenge dict and returns signed payment
            client: Optional existing httpx client (creates new if None)
            **kwargs: Additional arguments passed to httpx.Client or AsyncClient
            
        Example:
            async def my_handler(challenge):
                return await sign_payment(challenge)
                
            client = X402HttpxClient(handle_x402=my_handler)
            response = await client.get("https://api.example.com/protected")
        """
        self.handle_x402 = handle_x402
        
        if client is None:
            # Determine if async based on handle_x402
            import asyncio
            import inspect
            if inspect.iscoroutinefunction(handle_x402):
                self.client = AsyncClient(**kwargs)
                self._is_async = True
            else:
                self.client = Client(**kwargs)
                self._is_async = False
        else:
            self.client = client
            self._is_async = isinstance(client, AsyncClient)
        
        self._original_request = self.client.request
        self._original_get = self.client.get
        self._original_post = self.client.post
        self._original_put = self.client.put
        self._original_delete = self.client.delete
        self._original_patch = self.client.patch
    
    async def _handle_402_async(self, response: httpx.Response, method: str, url: str, **kwargs):
        """Handle 402 response asynchronously"""
        if response.status_code == 402:
            try:
                data = response.json()
                challenge = data.get("challenge")
                
                if challenge:
                    payment_header = await self.handle_x402(challenge)
                    
                    if payment_header:
                        headers = dict(kwargs.get("headers", {}))
                        headers["X-PAYMENT"] = payment_header
                        kwargs["headers"] = headers
                        
                        # Retry request
                        return await self._original_request(method, url, **kwargs)
            except (ValueError, KeyError, json.JSONDecodeError):
                pass
        
        return response
    
    def _handle_402_sync(self, response: httpx.Response, method: str, url: str, **kwargs):
        """Handle 402 response synchronously"""
        if response.status_code == 402:
            try:
                data = response.json()
                challenge = data.get("challenge")
                
                if challenge:
                    payment_header = self.handle_x402(challenge)
                    
                    if payment_header:
                        headers = dict(kwargs.get("headers", {}))
                        headers["X-PAYMENT"] = payment_header
                        kwargs["headers"] = headers
                        
                        # Retry request
                        return self._original_request(method, url, **kwargs)
            except (ValueError, KeyError, json.JSONDecodeError):
                pass
        
        return response
    
    def request(self, method: str, url: str, **kwargs):
        """Make request with 402 handling"""
        if self._is_async:
            async def _request():
                response = await self._original_request(method, url, **kwargs)
                return await self._handle_402_async(response, method, url, **kwargs)
            return _request()
        else:
            response = self._original_request(method, url, **kwargs)
            return self._handle_402_sync(response, method, url, **kwargs)
    
    def get(self, url: str, **kwargs):
        """GET request with 402 handling"""
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs):
        """POST request with 402 handling"""
        return self.request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs):
        """PUT request with 402 handling"""
        return self.request("PUT", url, **kwargs)
    
    def delete(self, url: str, **kwargs):
        """DELETE request with 402 handling"""
        return self.request("DELETE", url, **kwargs)
    
    def patch(self, url: str, **kwargs):
        """PATCH request with 402 handling"""
        return self.request("PATCH", url, **kwargs)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if not self._is_async:
            self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._is_async:
            await self.client.aclose()

