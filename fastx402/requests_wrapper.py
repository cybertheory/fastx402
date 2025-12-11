"""
Wrapper for requests library to handle x402 payment challenges
"""

import json
from typing import Callable, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def patch_requests(
    handle_x402: Callable[[Dict[str, Any]], str],
    session: Optional[requests.Session] = None
) -> requests.Session:
    """
    Patch a requests Session to automatically handle 402 payment challenges
    
    Args:
        handle_x402: Callback function that receives challenge dict and returns signed payment header
        session: Optional existing session to patch (creates new if None)
        
    Returns:
        Patched requests.Session
        
    Example:
        def my_handler(challenge):
            # Sign challenge and return X-PAYMENT header value
            return signed_payment_header
            
        session = patch_requests(handle_x402=my_handler)
        response = session.get("https://api.example.com/protected")
    """
    if session is None:
        session = requests.Session()
    
    # Store original request method
    original_request = session.request
    
    def x402_request(method, url, **kwargs):
        # Make initial request
        response = original_request(method, url, **kwargs)
        
        # Handle 402 Payment Required
        if response.status_code == 402:
            try:
                data = response.json()
                challenge = data.get("challenge")
                
                if not challenge:
                    return response
                
                # Get signed payment from handler
                payment_header = handle_x402(challenge)
                
                if not payment_header:
                    return response
                
                # Retry request with X-PAYMENT header
                headers = kwargs.get("headers", {})
                if isinstance(headers, dict):
                    headers = headers.copy()
                else:
                    headers = dict(headers)
                
                headers["X-PAYMENT"] = payment_header
                kwargs["headers"] = headers
                
                # Retry the request
                response = original_request(method, url, **kwargs)
                
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                # If parsing fails, return original 402 response
                pass
        
        return response
    
    # Replace request method
    session.request = x402_request
    
    # Also patch common methods
    session.get = lambda url, **kwargs: session.request("GET", url, **kwargs)
    session.post = lambda url, **kwargs: session.request("POST", url, **kwargs)
    session.put = lambda url, **kwargs: session.request("PUT", url, **kwargs)
    session.delete = lambda url, **kwargs: session.request("DELETE", url, **kwargs)
    session.patch = lambda url, **kwargs: session.request("PATCH", url, **kwargs)
    
    return session


class X402Session(requests.Session):
    """
    Requests Session subclass with built-in x402 support
    """
    
    def __init__(self, handle_x402: Callable[[Dict[str, Any]], str], *args, **kwargs):
        """
        Initialize x402-enabled session
        
        Args:
            handle_x402: Callback function for handling payment challenges
        """
        super().__init__(*args, **kwargs)
        self.handle_x402 = handle_x402
        self._original_request = super().request
    
    def request(self, method, url, **kwargs):
        """Override request to handle 402 challenges"""
        response = self._original_request(method, url, **kwargs)
        
        if response.status_code == 402:
            try:
                data = response.json()
                challenge = data.get("challenge")
                
                if challenge:
                    payment_header = self.handle_x402(challenge)
                    
                    if payment_header:
                        headers = kwargs.get("headers", {})
                        if isinstance(headers, dict):
                            headers = headers.copy()
                        else:
                            headers = dict(headers)
                        
                        headers["X-PAYMENT"] = payment_header
                        kwargs["headers"] = headers
                        
                        # Retry request
                        response = self._original_request(method, url, **kwargs)
            except (ValueError, KeyError, json.JSONDecodeError):
                pass
        
        return response

