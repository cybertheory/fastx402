"""
Easy signature generation functions for payment challenges
"""

from typing import Optional
from fastx402.types import PaymentChallenge, PaymentSignature
from fastx402.client.waas.base import WAASProvider
from fastx402.client.waas.config import get_waas_provider


async def sign_payment_challenge(
    challenge: PaymentChallenge,
    waas_provider: Optional[WAASProvider] = None
) -> Optional[PaymentSignature]:
    """
    Easy function to sign a payment challenge
    
    This function can work with:
    - WAAS providers (embedded wallets)
    - Global configured provider
    
    Args:
        challenge: Payment challenge to sign
        waas_provider: Optional WAAS provider for embedded wallet signing
        
    Returns:
        PaymentSignature with signature, or None if signing fails
        
    Example:
        ```python
        from fastx402.client.waas import PrivyWAASProvider, sign_payment_challenge
        from privy import PrivyClient
        
        # Initialize Privy client
        privy_client = PrivyClient(app_id="your-app-id")
        await privy_client.ready()
        
        # Create WAAS provider
        waas = PrivyWAASProvider(privy_client=privy_client)
        
        # Sign a challenge
        signature = await sign_payment_challenge(challenge, waas_provider=waas)
        
        # Or configure globally
        from fastx402.client.waas.config import set_waas_provider
        set_waas_provider(waas)
        signature = await sign_payment_challenge(challenge)
        ```
    """
    if waas_provider:
        return await waas_provider.sign_payment(challenge)
    
    # Try to get from global config
    provider = get_waas_provider()
    if provider:
        return await provider.sign_payment(challenge)
    
    raise ValueError("No WAAS provider available. Please provide a waas_provider or configure one globally using set_waas_provider().")

