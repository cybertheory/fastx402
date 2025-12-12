"""
Server-side x402 payment challenge and verification
"""

import os
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastx402.types import PaymentChallenge, PaymentConfig, PaymentVerificationResult
from fastx402.utils import encode_payment_message, verify_signature, generate_nonce


class X402Server:
    """Server for issuing 402 challenges and verifying payments"""
    
    def __init__(
        self,
        config: Optional[PaymentConfig] = None
    ):
        """
        Initialize x402 server
        
        Args:
            config: Payment configuration (or loads from env)
        """
        if config is None:
            config = self._load_config_from_env()
        
        self.config = config
    
    @staticmethod
    def _load_config_from_env() -> PaymentConfig:
        """Load configuration from environment variables"""
        from dotenv import load_dotenv
        load_dotenv()
        
        merchant_address = os.getenv("X402_MERCHANT_ADDRESS")
        if not merchant_address:
            raise ValueError("X402_MERCHANT_ADDRESS environment variable is required")
        
        return PaymentConfig(
            merchant_address=merchant_address,
            chain_id=int(os.getenv("X402_CHAIN_ID", "8453")),
            currency=os.getenv("X402_CURRENCY", "USDC"),
        )
    
    def create_challenge(
        self,
        price: str,
        currency: Optional[str] = None,
        chain_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> PaymentChallenge:
        """
        Create a payment challenge
        
        Args:
            price: Price in token units
            currency: Currency symbol (defaults to config)
            chain_id: Chain ID (defaults to config)
            description: Optional description
            
        Returns:
            PaymentChallenge
        """
        return PaymentChallenge(
            price=price,
            currency=currency or self.config.currency,
            chain_id=chain_id or self.config.chain_id,
            merchant=self.config.merchant_address,
            description=description,
            nonce=generate_nonce()
        )
    
    async def verify_payment_header(
        self,
        request: Request
    ) -> PaymentVerificationResult:
        """
        Verify X-PAYMENT header from request
        
        Args:
            request: FastAPI request object
            
        Returns:
            PaymentVerificationResult
        """
        payment_header = request.headers.get("X-PAYMENT")
        if not payment_header:
            return PaymentVerificationResult(
                valid=False,
                error="Missing X-PAYMENT header"
            )
        
        try:
            import json
            payment_data = json.loads(payment_header)
            
            signature = payment_data.get("signature")
            signer = payment_data.get("signer")
            challenge_dict = payment_data.get("challenge")
            
            if not all([signature, signer, challenge_dict]):
                return PaymentVerificationResult(
                    valid=False,
                    error="Invalid payment header format"
                )
            
            challenge = PaymentChallenge(**challenge_dict)
            
            # Verify signature cryptographically (same for all modes)
            message_hash = encode_payment_message(challenge.model_dump())
            is_valid = verify_signature(signature, message_hash, signer)
            
            if not is_valid:
                return PaymentVerificationResult(
                    valid=False,
                    error="Signature verification failed"
                )
            
            return PaymentVerificationResult(
                valid=True,
                signer=signer
            )
        except Exception as e:
            return PaymentVerificationResult(
                valid=False,
                error=f"Verification error: {str(e)}"
            )
    
    def issue_402_response(
        self,
        challenge: PaymentChallenge
    ) -> JSONResponse:
        """
        Create HTTP 402 Payment Required response
        
        Args:
            challenge: Payment challenge
            
        Returns:
            JSONResponse with 402 status
        """
        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment Required",
                "challenge": challenge.model_dump()
            },
            headers={
                "X-Payment-Required": "true",
                "Content-Type": "application/json"
            }
        )

