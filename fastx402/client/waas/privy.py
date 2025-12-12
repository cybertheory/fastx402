"""
Privy WAAS provider implementation for client-side Python
"""

from typing import Optional
from fastx402.types import PaymentChallenge, PaymentSignature
from fastx402.client.waas.base import WAASProvider
from fastx402.utils import get_eip712_domain, get_eip712_types, create_payment_message


class PrivyWAASProvider(WAASProvider):
    """
    Privy wallet-as-a-service provider for client-side Python
    
    This provider uses Privy's Python SDK to sign payment challenges
    with embedded wallets.
    
    Example:
        ```python
        from privy import PrivyClient
        from fastx402.client.waas import PrivyWAASProvider
        
        # Initialize Privy client
        privy_client = PrivyClient(app_id="your-app-id")
        await privy_client.ready()
        
        # Create WAAS provider
        waas = PrivyWAASProvider(privy_client=privy_client)
        
        # Sign a payment challenge
        challenge = PaymentChallenge(...)
        signature = await waas.sign_payment(challenge)
        ```
    """
    
    def __init__(self, privy_client):
        """
        Initialize Privy WAAS provider
        
        Args:
            privy_client: Initialized Privy client instance from @privy/python SDK
        """
        self.privy_client = privy_client
        if not privy_client:
            raise ValueError("Privy client is required")
    
    async def sign_payment(
        self,
        challenge: PaymentChallenge
    ) -> Optional[PaymentSignature]:
        """
        Sign a payment challenge using Privy's embedded wallet
        
        Args:
            challenge: Payment challenge to sign
            
        Returns:
            PaymentSignature with signature, or None if signing fails
        """
        try:
            # Get the user's embedded wallet from Privy
            user = await self.privy_client.get_user()
            if not user:
                return None
            
            # Get embedded wallet
            embedded_wallet = user.get_embedded_wallet()
            if not embedded_wallet:
                return None
            
            # Prepare EIP-712 structured data
            domain = get_eip712_domain(challenge.chain_id)
            types = get_eip712_types()
            message = create_payment_message(
                challenge.model_dump() if hasattr(challenge, 'model_dump') else challenge.dict()
            )
            
            # Sign using Privy's sign_typed_data method
            # Note: Actual API may vary based on Privy Python SDK version
            signature = await embedded_wallet.sign_typed_data(
                domain=domain,
                types=types,
                message=message,
                primary_type="Payment"
            )
            
            # Get wallet address
            address = await embedded_wallet.get_address()
            
            return PaymentSignature(
                signature=signature,
                signer=address,
                challenge=challenge
            )
        except Exception as e:
            # Log error for debugging
            import logging
            logging.error(f"Failed to sign payment with Privy: {e}")
            return None
    
    async def get_wallet_address(self) -> Optional[str]:
        """
        Get the wallet address for the current Privy user
        
        Returns:
            Wallet address or None
        """
        try:
            user = await self.privy_client.get_user()
            if not user:
                return None
            
            embedded_wallet = user.get_embedded_wallet()
            if not embedded_wallet:
                return None
            
            return await embedded_wallet.get_address()
        except Exception:
            return None
    
    async def is_ready(self) -> bool:
        """
        Check if Privy client is ready and user has a wallet
        
        Returns:
            True if ready, False otherwise
        """
        try:
            user = await self.privy_client.get_user()
            if not user:
                return False
            
            embedded_wallet = user.get_embedded_wallet()
            return embedded_wallet is not None
        except Exception:
            return False


