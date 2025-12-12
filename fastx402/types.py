"""
Type definitions for x402 payment challenges and configurations
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PaymentChallenge(BaseModel):
    """HTTP 402 Payment Required challenge structure"""
    
    price: str = Field(..., description="Price in token units (e.g., '0.01')")
    currency: str = Field(..., description="Token symbol (e.g., 'USDC')")
    chain_id: int = Field(..., description="Chain ID (e.g., 8453 for Base)")
    merchant: str = Field(..., description="Merchant wallet address")
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    description: Optional[str] = Field(None, description="Optional payment description")
    nonce: Optional[str] = Field(None, description="Optional nonce for replay protection")
    
    class Config:
        json_schema_extra = {
            "example": {
                "price": "0.01",
                "currency": "USDC",
                "chain_id": 8453,
                "merchant": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "timestamp": 1699123456,
                "description": "API access fee"
            }
        }


class PaymentSignature(BaseModel):
    """Signed payment payload"""
    
    signature: str = Field(..., description="EIP-712 signature (hex)")
    signer: str = Field(..., description="Signer wallet address")
    challenge: PaymentChallenge = Field(..., description="Original challenge")
    message_hash: Optional[str] = Field(None, description="EIP-712 message hash")


class PaymentConfig(BaseModel):
    """Global payment configuration"""
    
    merchant_address: str
    chain_id: int = 8453
    currency: str = "USDC"


class PaymentVerificationResult(BaseModel):
    """Result of payment signature verification"""
    
    valid: bool
    signer: Optional[str] = None
    error: Optional[str] = None
    tx_hash: Optional[str] = None  # For embedded mode transactions

