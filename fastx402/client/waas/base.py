"""
Base interface for client-side Wallet-as-a-Service (WAAS) providers
"""

from abc import ABC, abstractmethod
from typing import Optional
from fastx402.types import PaymentChallenge, PaymentSignature


class WAASProvider(ABC):
    """Abstract base class for client-side WAAS providers"""
    
    @abstractmethod
    async def sign_payment(
        self,
        challenge: PaymentChallenge
    ) -> Optional[PaymentSignature]:
        """
        Sign a payment challenge using the WAAS provider
        
        Args:
            challenge: The payment challenge to sign
            
        Returns:
            PaymentSignature with signature, or None if signing fails
        """
        pass
    
    @abstractmethod
    async def get_wallet_address(self) -> Optional[str]:
        """
        Get the wallet address for the current user
        
        Returns:
            Wallet address or None
        """
        pass
    
    @abstractmethod
    async def is_ready(self) -> bool:
        """
        Check if the provider is ready/connected
        
        Returns:
            True if ready, False otherwise
        """
        pass


