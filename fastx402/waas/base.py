"""
Base interface for Wallet-as-a-Service (WAAS) providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fastx402.types import PaymentChallenge, PaymentVerificationResult


class WAASProvider(ABC):
    """Abstract base class for WAAS providers"""
    
    @abstractmethod
    async def verify_payment(
        self,
        challenge: PaymentChallenge,
        signature: str,
        signer: str
    ) -> PaymentVerificationResult:
        """
        Verify a payment signature using the WAAS provider
        
        Args:
            challenge: The payment challenge
            signature: EIP-712 signature
            signer: Signer wallet address
            
        Returns:
            PaymentVerificationResult with validation status
        """
        pass
    
    @abstractmethod
    async def get_wallet_address(
        self,
        user_id: str
    ) -> Optional[str]:
        """
        Get wallet address for a user ID
        
        Args:
            user_id: User identifier
            
        Returns:
            Wallet address or None
        """
        pass
    
    @abstractmethod
    async def sign_payment(
        self,
        challenge: PaymentChallenge,
        user_id: str
    ) -> Optional[str]:
        """
        Sign a payment challenge on behalf of a user (embedded mode)
        
        Args:
            challenge: The payment challenge
            user_id: User identifier
            
        Returns:
            Signature or None if signing fails
        """
        pass

