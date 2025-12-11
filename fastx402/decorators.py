"""
Decorators for protecting FastAPI endpoints with x402 payments
"""

from functools import wraps
from typing import Optional, Callable, Any
from fastapi import Request, HTTPException, status
from fastx402.server import X402Server
from fastx402.types import PaymentConfig, PaymentVerificationResult


# Global server instance (can be configured)
_server_instance: Optional[X402Server] = None


def configure_server(config: Optional[PaymentConfig] = None, waas_provider=None):
    """Configure global x402 server instance"""
    global _server_instance
    _server_instance = X402Server(config=config, waas_provider=waas_provider)


def get_server() -> X402Server:
    """Get or create global server instance"""
    global _server_instance
    if _server_instance is None:
        _server_instance = X402Server()
    return _server_instance


def payment_required(
    price: str,
    currency: Optional[str] = None,
    chain_id: Optional[int] = None,
    description: Optional[str] = None
):
    """
    Decorator to require payment for a FastAPI endpoint
    
    Args:
        price: Price in token units (e.g., "0.01")
        currency: Currency symbol (defaults to config)
        chain_id: Chain ID (defaults to config)
        description: Optional payment description
        
    Example:
        @app.get("/paid")
        @payment_required(price="0.01", currency="USDC", chain_id="8453")
        def paid_route():
            return {"msg": "you paid!"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            server = get_server()
            
            # Check for X-PAYMENT header
            payment_header = request.headers.get("X-PAYMENT")
            
            if not payment_header:
                # Issue 402 challenge
                challenge = server.create_challenge(
                    price=price,
                    currency=currency,
                    chain_id=chain_id,
                    description=description
                )
                return server.issue_402_response(challenge)
            
            # Verify payment
            verification = await server.verify_payment_header(request)
            
            if not verification.valid:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=verification.error or "Invalid payment"
                )
            
            # Payment verified, proceed with route handler
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

